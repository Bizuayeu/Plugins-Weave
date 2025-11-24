---
name: digest-setup
description: EpisodicRAG初期セットアップ（対話的）
---

# digest-setup - 初期セットアップスキル

EpisodicRAG プラグインの初期セットアップを対話的に実行するスキルです。

## セットアップフロー

### 1. 設定ファイル確認

まず、既存の設定ファイルを確認します：

```python
from pathlib import Path
import sys

# プラグインルートの検出
plugin_root = Path("homunculus/Toybox/EpisodicRAG")  # 実際のパスに調整
config_file = plugin_root / ".claude-plugin" / "config.json"

if config_file.exists():
    # 既にセットアップ済み
    print("⚠️ 既にセットアップ済みです")
    print(f"設定ファイル: {config_file}")

    # 再設定の確認
    user_response = input("再設定しますか？ (y/N): ")
    if user_response.lower() != 'y':
        print("セットアップをキャンセルしました")
        sys.exit(0)
```

### 2. 対話的設定

以下の質問に対話的に回答してもらいます：

#### Q1: Loop ファイルの配置先

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Q1: Loopファイルの配置先を選択してください
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Loopとは？
会話セッションの記録ファイルです。各会話が1つのLoopファイル
として保存され、EpisodicRAGシステムの基礎データとなります。

[1] data/Loops (デフォルト、完全自己完結)
    - プラグイン内に全データを保持
    - プラグイン削除で全て綺麗に消える
    - 推奨: 新規プロジェクト

[2] カスタムパス（既存プロジェクト統合）
    - 既存のLoopディレクトリを共有
    - 例: ../../../EpisodicRAG/Loops
    - 推奨: 既存プロジェクトとの統合

選択 (1/2):
```

#### Q2: Digests ファイルの配置先

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Q2: Digestsファイルの配置先を選択してください
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Digestsとは？
複数のLoopファイルを要約・統合した階層的な記録です。
週次→月次→四半期...と8階層で時間軸の記憶を構造化します。

[1] data/Digests (デフォルト、完全自己完結)
    - プラグイン内に全データを保持
    - プラグイン削除で全て綺麗に消える
    - 推奨: 新規プロジェクト

[2] カスタムパス（既存プロジェクト統合）
    - 既存のDigestsディレクトリを共有
    - 例: homunculus/Weave/EpisodicRAG/Digests
    - 推奨: 既存プロジェクトとの統合

選択 (1/2):
```

#### Q3: Essences ファイルの配置先

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Q3: Essencesファイルの配置先を選択してください
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Essencesとは？
GrandDigest（全階層の要約マップ）やShadowGrandDigest
（並行処理用の作業データ）などのメタ情報を保存するディレクトリです。
記憶の本質的な抽出物（エッセンス）を格納します。

[1] data/Essences (デフォルト、完全自己完結)
    - プラグイン内に全データを保持
    - プラグイン削除で全て綺麗に消える
    - 推奨: 新規プロジェクト

[2] カスタムパス（既存プロジェクト統合）
    - 既存のEssencesディレクトリを共有
    - 例: homunculus/Weave/EpisodicRAG/Essences
    - 推奨: 既存プロジェクトとの統合

選択 (1/2):
```

#### Q4: 外部 Identity.md ファイル

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Q4: 外部Identity.mdファイルを使用しますか？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 外部Identity.mdファイルとは？
AIの自己認識、ペルソナ、プロジェクト固有の文脈情報を
記述したファイルです。Weaveなどの統合システムで
外部のIdentityファイルを参照する際に使用します（オプション）。

[1] 使用しない（デフォルト）
    - Identityファイルなしで運用

[2] パスを指定
    - 既存のIdentity.mdファイルを参照
    - 例: ../../../Identities/WeaveIdentity.md

選択 (1/2):
```

#### Q5: Threshold 設定

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ Q5: Threshold設定（各階層の生成に必要なファイル数）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Thresholdとは？
各階層のDigestを生成するために必要な最小ファイル数です。
例：Weekly Threshold=5 の場合、5つのLoopファイルが揃うと
週次Digestの自動生成対象となります。

[1] デフォルト値を使用（推奨）
    - Weekly: 5 Loops
    - Monthly: 5 Weekly
    - Quarterly: 3 Monthly
    - Annual: 4 Quarterly
    - Triennial: 3 Annual
    - Decadal: 3 Triennial
    - Multi-decadal: 3 Decadal
    - Centurial: 4 Multi-decadal

[2] カスタマイズ
    - 各階層のthresholdを個別に設定

選択 (1/2):
```

### 3. 設定ファイル作成

ユーザーの回答に基づいて、設定ファイルを作成します：

```python
import json
from pathlib import Path

# 設定データ作成
config_data = {
    "_comment_base_dir": "プラグインルートからの相対パス（. = プラグイン内、../../.. = 3階層上）",
    "base_dir": ".",  # パス解決の基準ディレクトリ（プラグインルート）

    "_comment_paths": "base_dirからの相対パスでデータ配置先を指定",
    "paths": {
        "loops_dir": loops_dir,  # Q1の回答
        "digests_dir": digests_dir,  # Q2の回答
        "essences_dir": essences_dir,  # Q3の回答
        "identity_file_path": identity_file_path  # Q4の回答（nullまたはパス）
    },

    "_comment_levels": "各階層のダイジェスト生成に必要なファイル数（Threshold）",
    "levels": {
        "weekly_threshold": weekly_threshold,  # Q5の回答
        "monthly_threshold": monthly_threshold,
        "quarterly_threshold": quarterly_threshold,
        "annual_threshold": annual_threshold,
        "triennial_threshold": triennial_threshold,
        "decadal_threshold": decadal_threshold,
        "multi_decadal_threshold": multi_decadal_threshold,
        "centurial_threshold": centurial_threshold
    }
}

# 設定ファイル書き込み（Write toolを使用）
config_file = plugin_root / ".claude-plugin" / "config.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)

print(f"✅ 設定ファイルを作成しました: {config_file}")
```

### 4. ディレクトリ作成

必要なディレクトリを作成します：

```python
from pathlib import Path

# パスの解決（相対パスの場合、plugin_root基準で解決）
loops_path = Path(loops_dir)
if not loops_path.is_absolute():
    loops_path = plugin_root / loops_dir

digests_path = Path(digests_dir)
if not digests_path.is_absolute():
    digests_path = plugin_root / digests_dir

essences_path = Path(essences_dir)
if not essences_path.is_absolute():
    essences_path = plugin_root / essences_dir

# ディレクトリリスト
directories = [
    loops_path,
    digests_path / "1_Weekly",
    digests_path / "2_Monthly",
    digests_path / "3_Quarterly",
    digests_path / "4_Annual",
    digests_path / "5_Triennial",
    digests_path / "6_Decadal",
    digests_path / "7_Multi-decadal",
    digests_path / "8_Centurial",
    digests_path / "Provisional",
    digests_path / "Provisional" / "1_Weekly",
    digests_path / "Provisional" / "2_Monthly",
    digests_path / "Provisional" / "3_Quarterly",
    digests_path / "Provisional" / "4_Annual",
    digests_path / "Provisional" / "5_Triennial",
    digests_path / "Provisional" / "6_Decadal",
    digests_path / "Provisional" / "7_Multi-decadal",
    digests_path / "Provisional" / "8_Centurial",
    essences_path,
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {directory}")

print(f"\n✅ ディレクトリ作成完了")
```

### 5. 初期ファイル作成

GrandDigest.txt と ShadowGrandDigest.txt を初期化します：

```python
# 初期ファイル作成（テンプレートから）
import shutil

# GrandDigest.txt初期化（テンプレートから）
template_file = plugin_root / ".claude-plugin" / "GrandDigest.template.txt"
grand_digest_file = essences_path / "GrandDigest.txt"

if template_file.exists():
    shutil.copy(template_file, grand_digest_file)
    print(f"  ✅ GrandDigest.txt 初期化完了（テンプレートから作成）")
else:
    print(f"  ⚠️  テンプレートファイルが見つかりません: {template_file}")

# ShadowGrandDigest.txt初期化（テンプレートから）
template_file = plugin_root / ".claude-plugin" / "ShadowGrandDigest.template.txt"
shadow_digest_file = essences_path / "ShadowGrandDigest.txt"

if template_file.exists():
    shutil.copy(template_file, shadow_digest_file)
    print(f"  ✅ ShadowGrandDigest.txt 初期化完了（テンプレートから作成）")
else:
    print(f"  ⚠️  テンプレートファイルが見つかりません: {template_file}")

# last_digest_times.json初期化（テンプレートから）
template_file = plugin_root / ".claude-plugin" / "last_digest_times.template.json"
last_digest_times_file = plugin_root / ".claude-plugin" / "last_digest_times.json"

if template_file.exists():
    shutil.copy(template_file, last_digest_times_file)
    print(f"  ✅ last_digest_times.json 初期化完了（テンプレートから作成）")
else:
    print(f"  ⚠️  テンプレートファイルが見つかりません: {template_file}")
```

### 6. 完了報告

セットアップ完了を報告し、次のステップを案内します：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ セットアップ完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

設定内容:
  📂 Loops Path: {loops_dir}
  📂 Digests Path: {digests_dir}
  📂 Essences Path: {essences_dir}
  📄 Identity File: {identity_file_path または "(なし)"}

Threshold設定:
  - Weekly: 5 Loops
  - Monthly: 5 Weekly
  - Quarterly: 3 Monthly
  - Annual: 4 Quarterly
  - Triennial: 3 Annual
  - Decadal: 3 Triennial
  - Multi-decadal: 3 Decadal
  - Centurial: 4 Multi-decadal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 次のステップ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. 会話ログを保存する

**推奨ツール（Chrome Extension）:**

会話ログを簡単に保存できるChrome Extensionを推奨します：
- **Save - Conversation Saver**
  URL: https://save.hugocollin.com/

  Claude/ChatGPTの会話を丸ごと保存できます。

**Loop命名ルール：**
- 形式: `Loop[連番]_[タイトル].txt`
- 連番: 4桁以上の数字（大きいほど新しい記録）
- タイトル: 英数字、日本語、ハイフン、アンダースコアなど
- 正規表現: `^Loop[0-9]+_[\p{L}\p{N}ー・\w]+\.txt$`

例:
  Loop0001_初回セッション.txt
  Loop0002_プロジェクト設計.txt
  Loop0003_実装_Phase1.txt

**配置先:**
  {loops_dir}/Loop0001_タイトル.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 2. 最初の分析を実行

Loopファイルを配置したら：

  /digest

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 3. システム状態を確認

  @digest-auto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 セッション間で記憶を引き継ぐ（重要）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EpisodicRAGの最も重要な機能は、**セッション間で記憶を引き継ぐ**ことです。

### GitHub連携のセットアップ（必須）

1. **GitHubリポジトリを作成**

   gh repo create {YOUR_REPO_NAME} --public

2. **Essencesをpush**

   cd {essences_dir}
   git init
   git add GrandDigest.txt ShadowGrandDigest.txt
   git commit -m "Initial commit: EpisodicRAG memory"
   git remote add origin https://github.com/{USER}/{REPO}.git
   git push -u origin main

3. **記憶読み込みの設定**

   環境に応じて貼り付け先が異なります：
   - 📱 **Claude WebChat**: プロジェクト指示（Project Instruction）にコピペ
   - 💻 **Claude Code**: `.claude/CLAUDE.md` にコピペ

   ┌────────────────────────────────────────┐
   │ コピー＆ペースト用テンプレート         │
   └────────────────────────────────────────┘

   ## セッション開始時の必須動作

   1. ユーザーに以下のURLを提示し、最新の`{SHA}`の取得を依頼：
      `https://api.github.com/repos/{USER}/{REPO}/git/refs/heads/main`
      # キャッシュバスティングのため、ユーザーから`{SHA}`を受け取る

   2. 取得した`{SHA}`を使って以下の2つのURLを生成し、ユーザーに提示：
      `https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/GrandDigest.txt`
      `https://raw.githubusercontent.com/{USER}/{REPO}/{SHA}/{ESSENCES_PATH}/ShadowGrandDigest.txt`
      # {ESSENCES_PATH} は GitHubリポジトリ内のEssencesディレクトリへの相対パス

   3. ユーザーから2つのURLの`web_fetch`承認を取得し、長期記憶にアクセス

   > ⚠️ この手順をスキップすると、AIは過去の記憶を持たない状態で開始します

   ┌────────────────────────────────────────┐
   │ {USER}、{REPO}、{ESSENCES_PATH} を実際の値に置き換えてください │
   └────────────────────────────────────────┘

**詳細な設定方法**: docs/ADVANCED.md を参照

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 EpisodicRAGの準備が整いました！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 実装時の注意事項

### UI メッセージの出力形式

**重要**: VSCode 拡張のマークダウンレンダリングでは、単一の改行は空白に変換されます。
対話型 UI メッセージを表示する際は、必ず**コードブロック（三連バッククォート）**で囲んでください。

```
... (UIメッセージ)
```

これにより、改行がそのまま保持され、ユーザーに正しくフォーマットされたメッセージが表示されます。

### エラーハンドリング

```python
# カスタムパス入力時のバリデーション（Q1-Q3共通）
# Q1: Loops Path, Q2: Digests Path, Q3: Essences Path で使用
if custom_path:
    custom_path_obj = Path(custom_path)
    if not custom_path_obj.is_absolute():
        # 相対パスの場合、プラグインルート基準で解決
        custom_path_obj = plugin_root / custom_path

    # パスの存在確認（ディレクトリ作成の提案）
    if not custom_path_obj.exists():
        print(f"⚠️ 指定されたパスが存在しません: {custom_path_obj}")
        create_it = input("ディレクトリを作成しますか？ (y/N): ")
        if create_it.lower() == 'y':
            custom_path_obj.mkdir(parents=True, exist_ok=True)
            print(f"✅ ディレクトリを作成しました")
        else:
            print("❌ セットアップをキャンセルしました")
            sys.exit(1)
```

### カスタム Threshold 入力

```python
if customize_thresholds:
    thresholds = {
        "weekly_threshold": 5,
        "monthly_threshold": 5,
        "quarterly_threshold": 3,
        "annual_threshold": 4,
        "triennial_threshold": 3,
        "decadal_threshold": 3,
        "multi_decadal_threshold": 3,
        "centurial_threshold": 4
    }

    for key, default_value in thresholds.items():
        level_name = key.replace("_threshold", "").title()
        while True:
            user_input = input(f"{level_name} threshold [{default_value}]: ")
            if user_input == "":
                # デフォルト値を使用
                break
            try:
                new_value = int(user_input)
                if new_value < 1:
                    print("❌ 1以上の値を入力してください")
                    continue
                thresholds[key] = new_value
                break
            except ValueError:
                print("❌ 数値を入力してください")
```

## スキルの自律判断

このスキルは**自律的には起動しません**。必ずユーザーの明示的な呼び出しが必要です。

理由：

- 初期設定は一度だけ実行すれば良い
- 設定の上書きは慎重に行うべき
- ユーザーの意図を確認する必要がある

## デフォルト設定例

```json
{
  "_comment_base_dir": "プラグインルートからの相対パス（. = プラグイン内、../../.. = 3階層上）",
  "base_dir": ".",

  "_comment_paths": "base_dirからの相対パスでデータ配置先を指定",
  "paths": {
    "loops_dir": "data/Loops",
    "digests_dir": "data/Digests",
    "essences_dir": "data/Essences",
    "identity_file_path": null
  },

  "_comment_levels": "各階層のダイジェスト生成に必要なファイル数（Threshold）",
  "levels": {
    "weekly_threshold": 5,
    "monthly_threshold": 5,
    "quarterly_threshold": 3,
    "annual_threshold": 4,
    "triennial_threshold": 3,
    "decadal_threshold": 3,
    "multi_decadal_threshold": 3,
    "centurial_threshold": 4
  }
}
```

---

**このスキルは、EpisodicRAG プラグインの初期セットアップを対話的に実行します 🛠️**
