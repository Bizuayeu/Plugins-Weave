#!/bin/bash
#
# EpisodicRAG Digest Auto-Generator (Plugin版 - config.py統合)
# ==============================================================
#
# 引数なし: 新Loopファイル検出 → ShadowGrandDigest.weeklyにプレースホルダー追加
#           → Claudeが即座に分析すべき（まだらボケ回避）
#
# 引数あり: ShadowGrandDigest → RegularDigest確定（分析は既に完了済み前提）
#
# 使用方法:
#   ./generate_digest_auto.sh                    # 新Loop検出 → Claudeが即分析
#   ./generate_digest_auto.sh weekly             # ShadowからRegular確定
#   ./generate_digest_auto.sh monthly
#   ./generate_digest_auto.sh quarterly
#   ./generate_digest_auto.sh annual
#   ./generate_digest_auto.sh triennial
#   ./generate_digest_auto.sh decadal
#   ./generate_digest_auto.sh multi_decadal
#   ./generate_digest_auto.sh centurial
#
# プロセスフロー:
#   1. /digest → 新Loopファイル検出、プレースホルダー追加
#   2. Claudeが即座に分析 → ShadowGrandDigest.$LEVEL更新（まだらボケ回避）
#      2-1: Context Loading
#        - Identity.md でClaudeの自己認識を把握
#        - GrandDigest.txt で全体文脈を把握
#        - ShadowGrandDigest.txt で今回の対象を確認
#      2-2: DigestAnalyzer分析 (並列実行)
#        - [!] CRITICAL: Recency Bias回避のため、全ファイルを並列分析
#        - 各source fileに対して個別のDigestAnalyzerを起動
#        - 既に分析済みのファイルも、今回改めて読み直す
#        - 大きなファイル(>25000トークン)は分割読み込みで全文取得
#        - DigestAnalyzerがlong/short両方を生成:
#          * digest_type (本質的テーマ、10-20文字)
#          * keywords (5個、各20-50文字)
#          * abstract.long (2400文字、overall用)
#          * abstract.short (1200文字、individual用)
#          * impression.long (800文字、overall用)
#          * impression.short (400文字、individual用)
#      2-3: Provisional保存 (次階層用individual_digests自動生成)
#        - save_provisional_digest.py実行
#        - short版を使用してindividual_digests作成
#        - 次階層のProvisionalファイル生成（次の確定時に自動マージ）
#      2-4: ShadowGrandDigest更新 (long版)
#        - Essences/ShadowGrandDigest.txt を開く
#        - プレースホルダーをlong版で置換
#        - 保存
#   3. Loop追加の度に /digest → Claudeが再分析（動的更新）
#   4. /digest $LEVEL → RegularDigestに確定、Provisionalマージ、GrandDigest更新
#
# 処理構造:
#                RegularDigest  ShadowGrandDigest  GrandDigest
#   Loop                        1(追加+分析)
#   Weekly       1(分析済)      3(カスケード)      2
#   Monthly      1(分析済)      3(カスケード)      2
#   Quarterly    1(分析済)      3(カスケード)      2
#   Annual       1(分析済)      3(カスケード)      2
#   Triennial    1(分析済)      3(カスケード)      2
#   Decadal      1(分析済)      3(カスケード)      2
#   Multi-dec    1(分析済)      3(カスケード)      2
#   Centurial    1(分析済)                         2

set -e  # エラーで即停止

# スクリプト自身のディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# config.pyからパスを取得（Python経由）
get_config_path() {
    local path_name="$1"
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from config import DigestConfig
config = DigestConfig()
print(getattr(config, '${path_name}_path'))
" 2>/dev/null || {
        echo "[ERROR] Failed to get $path_name from config.py" >&2
        exit 1
    }
}

# Identity.mdのパスを取得（オプション）
get_weave_identity() {
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from config import DigestConfig
config = DigestConfig()
path = config.get_identity_file_path()
print(path if path else '')
" 2>/dev/null
}

# 各パスを取得
ESSENCES_PATH=$(get_config_path "essences")
WEAVE_IDENTITY_PATH=$(get_weave_identity)
WEAVE_CORE_FILE="${WEAVE_IDENTITY_PATH:-$ESSENCES_PATH/Identity.md}"
GRAND_FILE="$ESSENCES_PATH/GrandDigest.txt"
SHADOW_FILE="$ESSENCES_PATH/ShadowGrandDigest.txt"

# エラー時のクリーンアップ関数
cleanup_on_error() {
    echo "[ERROR] Script failed. Template file preserved for retry: $TEMPLATE_FILE"
    # エラー時はテンプレートファイルを残して再実行可能にする
}

# 成功時のクリーンアップ関数
cleanup_on_success() {
    echo "[INFO] Finalization complete"
}

# エラー時のみクリーンアップを実行
trap cleanup_on_error ERR

# **文脈ファイルの表示（Claudeの自己認識のため、全モードで必須）**
echo "========================================"
echo "[Context: GrandDigest - Latest Overview]"
echo "========================================"
echo "[INFO] For contextual awareness..."
echo ""

# Identity.mdの表示（設定されている場合）
if [ -f "$WEAVE_CORE_FILE" ]; then
    cat "$WEAVE_CORE_FILE"
else
    echo "[INFO] Identity.md not configured (skipped)"
fi

# GrandDigest.txtの表示
if [ -f "$GRAND_FILE" ]; then
    cat "$GRAND_FILE"
else
    echo "[INFO] GrandDigest.txt not found yet (will be created)"
fi

echo ""
echo "========================================"
echo ""

# /digest コマンドのパラメータチェック
if [ $# -eq 0 ]; then
    # 引数なし: 新Loop検出 → プレースホルダー追加 → Claudeが即分析すべき
    echo "========================================"
    echo "New Loop Detection & Shadow Update"
    echo "========================================"
    echo ""

    # shadow_grand_digest.pyを実行（Plugin版）
    cd "$SCRIPT_DIR"
    python3 shadow_grand_digest.py

    # 更新後のShadowGrandDigestを表示
    echo ""
    echo "========================================"
    echo "[Updated: ShadowGrandDigest.weekly]"
    echo "========================================"

    if [ -f "$SHADOW_FILE" ]; then
        cat "$SHADOW_FILE"
    else
        echo "[INFO] ShadowGrandDigest.txt not found yet (created by script)"
    fi

    echo ""
    echo "========================================"
    echo ""

    echo "========================================"
    echo "[!] CRITICAL: Claude Analysis Required NOW"
    echo "========================================"
    echo ""
    echo "To avoid 'まだらボケ' (memory fragmentation):"
    echo "  1. DigestAnalyzerで分析（long/short両方生成）"
    echo "     @DigestAnalyzer ShadowGrandDigest.weeklyを分析してください"
    echo ""
    echo "  2. save_provisional_digest.py実行（Weekly用individual作成）"
    echo "     cd $SCRIPT_DIR"
    echo "     python3 save_provisional_digest.py weekly '<individual_digests JSON>' --append"
    echo "     ※ short版（abstract.short, impression.short）を使用"
    echo "     ※ --append: 既存Provisionalに追加（複数回/digestで追加する場合）"
    echo ""
    echo "  3. ShadowGrandDigest.txt更新（long版で置換）"
    echo "     統合ソース: current Shadow long + new Provisional short"
    echo "     メインエージェントが統合してShadow.overall_digest更新"
    echo "     Edit tool でプレースホルダーをlong版分析結果で置換"
    echo "     ※ long版（abstract.long, impression.long）を使用"
    echo ""
    echo "DigestAnalyzer出力形式:"
    echo "  - digest_type (10-20文字)"
    echo "  - keywords (5個、各20-50文字)"
    echo "  - abstract.long (2400文字、overall用)"
    echo "  - abstract.short (1200文字、individual用)"
    echo "  - impression.long (800文字、overall用)"
    echo "  - impression.short (400文字、individual用)"
    echo ""
    echo "Without immediate analysis, memory gap occurs!"
    echo "========================================"
    echo ""
    echo "========================================"
    echo "[!] DO NOT finalize yet!"
    echo "========================================"
    echo ""
    echo "Finalization requires multiple files accumulated:"
    echo "  - Weekly: typically 5 Loops"
    echo "  - Monthly: typically 5 Weekly digests"
    echo "  - etc."
    echo ""

    # ShadowGrandDigest.txtからファイル数をカウント
    if [ -f "$SHADOW_FILE" ]; then
        FILE_COUNT=$(grep -o '"Loop[0-9]*' "$SHADOW_FILE" | wc -l || echo "0")
        echo "Current shadow has $FILE_COUNT file(s)."
    else
        echo "Current shadow has 0 file(s)."
    fi

    echo ""
    echo "Keep adding files with /digest, then run:"
    echo "  /digest weekly   (when ready)"
    echo "========================================"
    echo ""
    exit 0
fi

if [ $# -ne 1 ]; then
    # 引数2個以上の場合: エラーメッセージで正しい使い方を案内
    echo "Usage: $0 [LEVEL]"
    echo ""
    echo "No arguments: Update ShadowGrandDigest for new Loop files"
    echo ""
    echo "With arguments:"
    echo "  LEVEL: weekly | monthly | quarterly | annual | triennial | decadal | multi_decadal | centurial"
    echo ""
    echo "Note: START_NUM and COUNT are no longer needed."
    echo "      The script reads directly from ShadowGrandDigest."
    exit 1
fi

LEVEL=$1    # 引数1個の場合: 以下の手順でRegularDigestを作成する！

# **手順1: ShadowGrandDigestの確認**
echo "========================================"
echo "EpisodicRAG Digest Finalization"
echo "========================================"
echo "Level: $LEVEL"
echo ""
echo "[手順 1/3] Checking ShadowGrandDigest..."
echo "========================================"

echo ""
echo "========================================"
echo "[Context: ShadowGrandDigest - Current State]"
echo "========================================"

if [ -f "$SHADOW_FILE" ]; then
    cat "$SHADOW_FILE"
else
    echo "[ERROR] ShadowGrandDigest.txt not found"
    echo "Run without arguments first to create it"
    exit 1
fi

echo ""
echo "========================================"
echo ""

# **手順2: ShadowGrandDigest状態確認**
echo "========================================"
echo "[手順 2/3] ShadowGrandDigest State Check"
echo "========================================"
echo ""
echo "[Claude] 以下の手順で状態確認してください："
echo ""
echo "1. ShadowGrandDigest.$LEVEL の内容を確認"
echo "   - overall_digest.source_files を取得"
echo "   - overall_digest.abstract を確認"
echo ""
echo "2. 状態判定（プレースホルダーの有無）:"
echo "   - abstract に '<!-- PLACEHOLDER -->' が含まれる → 【未分析状態】"
echo "   - プレースホルダーなし → 【分析済み状態】"
echo ""
echo "3. 状態に応じた処理:"
echo ""
echo "   【未分析状態】"
echo "     → DigestAnalyzerを並列起動してlong/short生成"
echo "     → 次階層用Provisional作成（save_provisional_digest.py実行）"
echo "     → タイトル提案とfinalize実行"
echo ""
echo "   【分析済み状態】"
echo "     → DigestAnalyzer起動は不要（既に完了済み）"
echo "     → Provisionalも作成済み"
echo "     → 手順3（タイトル提案）へ直接進む"
echo ""
echo "========================================"
echo ""
echo "※ DigestAnalyzer実行が必要な場合:"
echo "  - Loop/Weekly/Monthly等のファイルを読み込み"
echo "  - long/short両方を生成:"
echo "    * digest_type (本質的テーマ、10-20文字)"
echo "    * keywords (5個、各20-50文字)"
echo "    * abstract.long (2400文字、現階層overall用)"
echo "    * abstract.short (1200文字、次階層individual用)"
echo "    * impression.long (800文字、現階層overall用)"
echo "    * impression.short (400文字、次階層individual用)"
echo ""
echo "※ Provisional作成コマンド例:"
echo "  cd $SCRIPT_DIR"
echo "  python3 save_provisional_digest.py <next_level> '<individual_digests JSON>'"
echo ""
echo "========================================"

# **手順3: Claudeによるタイトル提案と確定**
echo ""
echo "========================================"
echo "[手順 3/3] Title Suggestion & Finalization"
echo "========================================"
echo ""
echo "[Claude] 以下の手順でダイジェストを確定してください："
echo ""
echo "1. ShadowGrandDigest.$LEVEL の内容に基づいてタイトルを提案"
echo "   - 手順2のlong版分析結果（digest_type, keywords, abstract.long）を考慮"
echo "   - **重要**: タイトルのみ提案（プレフィックスと番号は不要）"
echo ""
echo "2. ユーザーの承認を得る"
echo ""
echo "3. finalize_from_shadow.py実行（自動処理）:"
echo "   cd $SCRIPT_DIR && python3 finalize_from_shadow.py $LEVEL \"提案タイトル\""
echo ""
echo "   このコマンドが実行する処理:"
echo "     - RegularDigest作成（overall_digest生成）"
echo "     - 現階層のProvisionalDigestをRegularDigestにマージ"
echo "       ※ 手順2で作成済みのProvisionalを自動読み込み"
echo "       ※ individual_digestsの手動追加は不要"
echo "     - GrandDigest更新"
echo "     - 次レベルのShadowへカスケード"
echo "     - last_digest_times.json更新"
echo "     - Provisionalファイル削除（マージ後クリーンアップ）"
echo ""
echo "4. 完了確認"
echo "   - 生成されたRegularDigestファイルパスを表示"
echo "   - GrandDigest.txtの更新内容を確認"
echo ""
echo "*** タイトル提案の注意点 ***"
echo "  [OK] 正しい例: \"理論的深化・実装加速・社会発信\""
echo "  [NG] 誤った例: \"W0043_理論的深化...\" (プレフィックス不要)"
echo ""
echo "Prefix examples (自動付与されます):"
echo "  Weekly: W, Monthly: M, Quarterly: Q, Annual: A"
echo "  Triennial: T, Decadal: D, Multi-decadal: MD, Centurial: C"
echo ""
echo "========================================"
echo "[Waiting for Weave's response...]"
echo "========================================"
echo ""

# スクリプトはここで停止し、Claudeの応答を待つ
exit 0
