#!/bin/bash
# =============================================================================
# EpisodicRAG Plugin セットアップスクリプト
# =============================================================================
#
# 概要:
#   EpisodicRAGプラグインの対話型セットアップウィザード。
#   設定ファイルとディレクトリ構造を作成する。
#
# 使用方法:
#   ./setup.sh           # 対話型セットアップ
#   ./setup.sh --help    # 詳細ヘルプ表示
#
# 終了コード:
#   0   成功
#   1   エラー発生
#
# =============================================================================

set -e  # エラーで即停止

# --help オプション処理
show_help() {
    cat << 'EOF'
================================================================================
EpisodicRAG Plugin セットアップスクリプト - 詳細ヘルプ
================================================================================

【対話プロンプト】
  1. Loops directory (Loopファイルの配置先)
     - デフォルト: data/Loops (Plugin内)
     - 外部参照例: ../../../EpisodicRAG/Loops

  2. Identity file (オプション)
     - 外部プロジェクトのIdentityファイルパス
     - 例: ../../../Identities/Identity.md

【作成されるディレクトリ構造】
  .claude-plugin/config.json    設定ファイル
  data/Loops/                   Loopファイル格納（デフォルト選択時）
  data/Digests/                 ダイジェスト格納
    1_Weekly/Provisional/
    2_Monthly/Provisional/
    3_Quarterly/Provisional/
    4_Annual/Provisional/
    5_Triennial/Provisional/
    6_Decadal/Provisional/
    7_Multi-decadal/Provisional/
    8_Centurial/Provisional/
  data/Essences/                エッセンスファイル
    GrandDigest.txt
    ShadowGrandDigest.txt

【依存関係】
  - Python 3
  - jq (オプション)
    * jqがある場合: 正確なJSON編集
    * jqがない場合: sedで単純置換（複雑なパスには非推奨）

【セットアップ完了後の確認】
  python -m interfaces.digest_setup check

  出力例 (JSON):
    {
      "status": "configured",
      "config_exists": true,
      "directories_exist": true,
      "config_file": "/path/to/.claude-plugin/config.json",
      "message": "Setup already completed"
    }

================================================================================
EOF
    exit 0
}

# 引数チェック
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
fi

# Pluginルート検出（このスクリプトの親ディレクトリ）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PLUGIN_DIR" || exit 1

echo "========================================"
echo "EpisodicRAG Plugin Setup"
echo "========================================"
echo ""
echo "Plugin Root: $PLUGIN_DIR"
echo ""

# 設定ファイルパス（Plugin内）
CONFIG_FILE=".claude-plugin/config.json"
TEMPLATE_FILE=".claude-plugin/config.template.json"

# 既存設定ファイルの確認
if [ -f "$CONFIG_FILE" ]; then
    echo "[WARNING] Config file already exists: $CONFIG_FILE"
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Setup cancelled"
        exit 0
    fi
fi

# 設定の入力
echo "Configuration Settings"
echo "----------------------"
echo ""

# 1. Loops directory
echo "1. Loops directory (Loopファイルの配置先)"
echo "   - Default: data/Loops (Plugin内)"
echo "   - External: ../../../EpisodicRAG/Loops (既存プロジェクトを共有)"
echo ""
read -p "Loops directory [data/Loops]: " LOOPS_DIR
LOOPS_DIR=${LOOPS_DIR:-data/Loops}
echo ""

# 2. Identity file (optional)
echo "2. Identity file (オプション - 外部プロジェクトのidentityファイル)"
echo "   - Default: none (null)"
echo "   - Example: ../../../Identities/Identity.md"
echo ""
read -p "Identity file path [press Enter to skip]: " IDENTITY_FILE
echo ""

# テンプレートからconfig.jsonを作成
echo "[INFO] Creating config.json from template..."
cp "$TEMPLATE_FILE" "$CONFIG_FILE"

# jq がある場合は使用、なければ sed で置換
if command -v jq &> /dev/null; then
    # jq を使った JSON 編集
    jq --arg loops "$LOOPS_DIR" '.paths.loops_dir = $loops' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

    if [ -n "$IDENTITY_FILE" ]; then
        jq --arg identity "$IDENTITY_FILE" '.paths.identity_file_path = $identity' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    fi
else
    # sed を使った単純置換
    sed -i.bak "s|\"data/Loops\"|\"$LOOPS_DIR\"|" "$CONFIG_FILE"

    if [ -n "$IDENTITY_FILE" ]; then
        sed -i.bak "s|\"identity_file_path\": null|\"identity_file_path\": \"$IDENTITY_FILE\"|" "$CONFIG_FILE"
    fi

    rm -f "$CONFIG_FILE.bak"
fi

echo "[OK] Config file created: $CONFIG_FILE"

# Plugin用ディレクトリ作成
echo ""
echo "Creating Plugin directories..."

# Loops ディレクトリは Plugin 内の場合のみ作成
if [[ "$LOOPS_DIR" == data/Loops* ]]; then
    mkdir -p "data/Loops"
fi

mkdir -p "data/Digests"/{1_Weekly,2_Monthly,3_Quarterly,4_Annual,5_Triennial,6_Decadal,7_Multi-decadal,8_Centurial}/Provisional
mkdir -p "data/Essences"

# GrandDigest/ShadowGrandDigest の初期ファイル作成
if [ ! -f "data/Essences/GrandDigest.txt" ]; then
    echo '{"metadata": {"version": "1.0"}, "levels": {"weekly": [], "monthly": [], "quarterly": [], "annual": [], "triennial": [], "decadal": [], "multi_decadal": [], "centurial": []}}' > "data/Essences/GrandDigest.txt"
    echo "[INFO] Created empty GrandDigest.txt"
fi

if [ ! -f "data/Essences/ShadowGrandDigest.txt" ]; then
    echo '{"metadata": {"last_updated": "", "version": "1.0"}, "shadow_digests": {}}' > "data/Essences/ShadowGrandDigest.txt"
    echo "[INFO] Created empty ShadowGrandDigest.txt"
fi

echo "[OK] Plugin data directories created"

# パス確認表示（digest_setup経由で取得）
echo ""
echo "========================================"
echo "Setup completed!"
echo "========================================"
echo ""

# digest_setup経由でパス表示
python -m interfaces.digest_setup check

echo ""
echo "========================================"
echo "Next steps:"
echo "========================================"
echo ""
echo "1. Place Loop files in: $LOOPS_DIR"
echo ""
echo "2. Test digest generation:"
echo "   cd $PLUGIN_DIR/scripts"
echo "   python -m application.grand.shadow_grand_digest"
echo ""
echo "3. Use Plugin scripts:"
echo "   bash scripts/generate_digest_auto.sh"
echo ""
echo "========================================"
echo ""
