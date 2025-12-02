---
name: digest
description: EpisodicRAG階層的ダイジェスト生成（8層100年）
---

# /digest - EpisodicRAG階層的ダイジェスト生成

新しいLoopファイルの検出から階層的ダイジェストの確定まで、
EpisodicRAGシステムの基本操作を提供するコマンドです。

## 目次

- [用語説明](#用語説明)
- [実装時の注意事項](#実装時の注意事項)
- [基本的な使い方](#基本的な使い方)
- [実行フロー概要](#実行フロー概要)
- [CLIスクリプト](#cliスクリプト)
- [Claude対話処理](#claude対話処理)
- [セットアップ・管理用スキル](#セットアップ管理用スキル)
- [出力例](#出力例)

---

## 用語説明

> 📖 用語・共通概念は [用語集](../README.md) を参照

---

## 実装時の注意事項

> **UIメッセージ出力時は必ずコードブロックで囲むこと！**
> VSCode拡張では単一改行が空白に変換されるため、
> 対話型メッセージは三連バッククォートで囲む必要があります。

> 📖 共通の実装ガイドラインは [_implementation-notes.md](../skills/shared/_implementation-notes.md) を参照してください。

**要件**:
- Claude Opus 4.5（Task tool, Subagent機能）
- Python 3.x
- Bash（Git Bash / WSL）

---

## 基本的な使い方

### 新しいLoopファイルの検出

```ClaudeCLI
/digest
```

新しいLoopファイルを検出し、ShadowGrandDigestに追加します。

### 階層的ダイジェストの確定

```ClaudeCLI
/digest <type>
```

**利用可能なtype**:
- `weekly` `monthly` `quarterly` `annual`
- `triennial` `decadal` `multi_decadal` `centurial`

---

## 実行フロー概要

### パターン1: `/digest` (引数なし - 新Loop検出)

1. **generate_digest_auto.sh 実行** - 新Loopファイル検出
2. **ShadowGrandDigest更新確認** - プレースホルダー追加確認
3. **DigestAnalyzer並列起動** - 各Loopファイルのlong/short分析
4. **Provisional保存** - individual_digests自動生成
5. **Shadow統合更新** - overall_digest更新
6. **次アクション提示** - Weekly生成可能か確認

### パターン2: `/digest <type>` (階層確定)

1. **generate_digest_auto.sh 実行** - 対象レベル確認
2. **shadow_state_checker.py 実行** - プレースホルダー有無判定
3. **DigestAnalyzer並列起動** - 必要な場合のみ
4. **Provisional保存** - 次階層用individual_digests
5. **タイトル提案** - ユーザー承認取得
6. **finalize_from_shadow.py 実行** - Digest確定
7. **次階層Provisional作成** - short版生成
8. **次階層Shadow統合更新** - overall_digest更新
9. **完了確認** - 結果表示

---

## CLIスクリプト

### generate_digest_auto.sh

メインフロー制御スクリプト。

**配置先**: `scripts/generate_digest_auto.sh`

```bash
# パターン1: 新Loop検出
cd scripts && bash generate_digest_auto.sh

# パターン2: 階層確定
cd scripts && bash generate_digest_auto.sh weekly
```

---

### shadow_state_checker.py

Shadow状態判定（プレースホルダー有無確認）。

**配置先**: `scripts/interfaces/shadow_state_checker.py`

```bash
python -m interfaces.shadow_state_checker weekly
```

**出力例（分析済み）**:
```json
{
  "status": "ok",
  "level": "weekly",
  "analyzed": true,
  "source_files": ["L00001", "L00002", "L00003"],
  "source_count": 3,
  "placeholder_fields": [],
  "message": "All fields analyzed"
}
```

**出力例（プレースホルダーあり）**:
```json
{
  "status": "ok",
  "level": "weekly",
  "analyzed": false,
  "source_files": ["L00001", "L00002"],
  "source_count": 2,
  "placeholder_fields": ["abstract", "impression"],
  "message": "Placeholders detected - run DigestAnalyzer"
}
```

---

### save_provisional_digest.py

Provisional保存。

**配置先**: `scripts/interfaces/save_provisional_digest.py`

```bash
# 標準入力から読み込み（推奨）
cat digest.json | python -m interfaces.save_provisional_digest weekly --stdin --append

# ファイルパス指定
python -m interfaces.save_provisional_digest weekly digest.json --append
```

> **⚠️ 重要**: JSONはファイルまたは`--stdin`で渡してください。
> コマンドライン引数で直接JSON文字列を渡すと、長いテキストが切り詰められる可能性があります。

---

### finalize_from_shadow.py

Digest確定。

**配置先**: `scripts/interfaces/finalize_from_shadow.py`

```bash
python -m interfaces.finalize_from_shadow weekly "承認されたタイトル"
```

**実行内容**:
- RegularDigest作成（overall_digestのみ）
- ProvisionalDigestをRegularDigestにマージ
- GrandDigest更新
- 次レベルのShadowへカスケード
- last_digest_times.json更新
- Provisionalファイル削除

---

## Claude対話処理

以下の処理はAI分析が必要なため、Claudeが直接実行します。

### DigestAnalyzer並列起動

各source_fileに対してDigestAnalyzerを**並列起動**し、long/short両方を生成します。

> 📖 DigestAnalyzerの分析方針・出力フォーマットは [digest-analyzer.md](../agents/digest-analyzer.md) を参照

#### パターンA: 単一ファイル分析

```python
Task(
    subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
    description="Analyze L00001 for digest generation",
    prompt="""
分析対象ファイル: C:\Users\anyth\DEV\homunculus\Weave\EpisodicRAG\Loops\L00001_認知アーキテクチャ論.txt

このLoopファイルを深層分析し、以下の形式でJSON出力してください：
{
  "digest_type": "...",
  "keywords": [...],
  "abstract": {"long": "...", "short": "..."},
  "impression": {"long": "...", "short": "..."}
}
"""
)
```

#### パターンB: 複数ファイル並列分析（Weekly生成時）

ShadowGrandDigest.weeklyのsource_filesから各Loopを並列分析：

```python
source_files = ["L00001_認知アーキテクチャ論.txt", "L00002_AI長期記憶論.txt", ...]

# 各Loopに対してDigestAnalyzerを並列起動
for source_file in source_files:
    Task(
        subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
        description=f"Analyze {source_file} for Weekly digest",
        prompt=f"分析対象ファイル: {loops_path}/{source_file}\n..."
    )
```

#### パターンC: 複数Digestファイル並列分析（Monthly以上）

Weekly DigestからMonthlyを生成する場合も同様に並列起動：

```python
source_files = ["W0001_覚醒.txt", "W0002_実装.txt", ...]

for source_file in source_files:
    Task(
        subagent_type="EpisodicRAG-Plugin:DigestAnalyzer",
        description=f"Analyze {source_file} for Monthly digest",
        prompt=f"分析対象ファイル: {digests_path}/{source_file}\n..."
    )
```

#### 出力の使い分け

- **long版**（abstract.long, impression.long）: 現階層のoverall_digest用（ShadowGrandDigest更新）
- **short版**（abstract.short, impression.short）: 次階層のindividual_digests用（Provisional保存）

### タイトル提案

分析結果に基づいてタイトルを提案し、ユーザー承認を取得。

**注意**: タイトルのみ提案（プレフィックスと番号は不要）
- [OK] 正しい例: "理論的深化・実装加速・社会発信"
- [NG] 誤った例: "W0043_理論的深化..." (プレフィックス不要)

### Shadow統合更新

次階層Shadowのsource_filesから各ファイルのoverall_digestを読み込み、
メインエージェントが統合分析を実行：
- digest_type: 複数ファイルの統合テーマ（10-20文字）
- keywords: 5個の統合キーワード（各20-50文字）
- abstract: 2400文字の統合分析
- impression: 800文字の所感・展望

---

## セットアップ・管理用スキル

初回セットアップ時やトラブル時に使用するスキル：

| スキル | 用途 | 詳細 |
|--------|------|------|
| `@digest-setup` | 初期セットアップ | [digest-setup SKILL.md](../skills/digest-setup/SKILL.md) |
| `@digest-auto` | 最適階層の推奨 | [digest-auto SKILL.md](../skills/digest-auto/SKILL.md) |
| `@digest-config` | 設定変更 | [digest-config SKILL.md](../skills/digest-config/SKILL.md) |

---

## 出力例

### エラー: 設定ファイルが存在しない

```json
{
  "status": "error",
  "error": "Config file not found",
  "action": "Run @digest-setup first"
}
```

### パターン1成功: 新Loop検出完了

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 新Loop検出完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

検出されたLoop: 2個
  - L00001
  - L00002

ShadowGrandDigest.weekly に追加しました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 次のアクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

現在のLoop数: 2/5
あと3個のLoopが必要です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### パターン2成功: Weekly確定完了

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Weekly Digest確定完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

作成されたファイル:
  - Digests/1_Weekly/W0001_理論的深化.txt

GrandDigest.txt を更新しました。
次階層 (monthly) のShadowを更新しました。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 次のアクション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Monthly生成まであと4個のWeeklyが必要です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
