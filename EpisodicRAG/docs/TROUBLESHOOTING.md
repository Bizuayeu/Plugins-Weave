# Troubleshooting - EpisodicRAG Plugin

このドキュメントでは、EpisodicRAGプラグインで発生する可能性のある**高度な問題**と、その解決方法について説明します。

**一般的な問題**（インストール、パス、Loopファイル検出など）については、[GUIDE.md](GUIDE.md) の「よくある問題と解決方法」セクションを参照してください。

---

## 目次

1. [高度なトラブルシューティング](#高度なトラブルシューティング)
   - [DigestAnalyzerエージェントが起動しない](#digestanalyzerエージェントが起動しない)
   - [individual_digestsが空になる](#individual_digestsが空になる)
   - [ShadowGrandDigestが更新されない](#shadowgranddigestが更新されない)
   - [階層的カスケードが動作しない](#階層的カスケードが動作しない)
   - [Digest生成時のJSON形式エラー](#digest生成時のjson形式エラー)
2. [システム状態の詳細診断](#システム状態の詳細診断)
3. [デバッグモード](#デバッグモード)
4. [サポート](#サポート)

---

## 高度なトラブルシューティング

### DigestAnalyzerエージェントが起動しない

**症状**: `@DigestAnalyzer`が起動しない、またはエラーが発生する

**確認ポイント**:

1. **config.jsonが存在するか**
   ```bash
   ls ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/.claude-plugin/config.json
   ```

2. **パス解決が正しいか**
   ```bash
   cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
   python scripts/config.py --show-paths
   ```

3. **GrandDigest.txtが存在するか**
   ```bash
   # 設定されているessences_dirを確認
   python scripts/config.py --show-paths

   # 該当パスのGrandDigest.txtを確認
   ls {essences_dir}/GrandDigest.txt
   ```

**解決方法**:

- **config.jsonが存在しない場合**: `@digest-setup`を実行
- **パス解決エラーの場合**: `@digest-config`で設定を確認・修正
- **GrandDigest.txtが存在しない場合**: 初回セットアップを実行
  ```bash
  @digest-setup
  ```

---

### individual_digestsが空になる

**症状**: Weekly Digestを生成したが、`individual_digests: []`となっている

**原因**: ProvisionalDigestファイルが生成されていない、または読み込めていない

**診断手順**:

1. **ProvisionalDigestディレクトリの確認**:
   ```bash
   # 設定されているdigests_dirを確認
   python scripts/config.py --show-paths

   # Provisionalディレクトリの内容確認
   ls {digests_dir}/Provisional/1_Weekly/
   ```

2. **W0001_Individual.txt形式のProvisionalファイルが存在するか確認**

3. **ファイルの内容が正しいか確認**:
   ```bash
   cat {digests_dir}/Provisional/1_Weekly/W0001_Individual.txt
   ```

**解決方法**:

**ケースA: Provisionalファイルが存在しない**

各Loopに対して`/digest`を再実行:
```bash
/digest  # Loop検出と分析
```

DigestAnalyzerが正しくindividual digestを生成しているか確認してください。

**ケースB: Provisionalファイルは存在するが読み込めていない**

ファイル形式が正しいか確認:
```bash
cat {digests_dir}/Provisional/1_Weekly/W0001_Individual.txt
```

期待される形式:
```
[Loop0001_タイトル.txt]
digest_type: ...
keywords: ...
abstract: ...
impression: ...

---

[Loop0002_タイトル.txt]
...
```

**ケースC: finalize_from_shadow.pyの実行エラー**

`/digest weekly` 実行時のエラーログを確認:
```bash
# 手動で finalize_from_shadow.py を実行してエラー詳細を確認
cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
python scripts/finalize_from_shadow.py weekly "テストタイトル"
```

---

### ShadowGrandDigestが更新されない

**症状**: 新しいLoopファイルを追加したが、ShadowGrandDigest.txtに反映されない

**確認ポイント**:

1. **last_digest_times.jsonの内容を確認**
   ```bash
   python scripts/config.py --show-paths  # digests_dirを確認
   cat {digests_dir}/last_digest_times.json
   ```

2. **新しいLoopファイルが検出されているか**
   ```bash
   @digest-auto
   ```

3. **ShadowGrandDigest.txtの構造確認**
   ```bash
   python scripts/config.py --show-paths  # essences_dirを確認
   cat {essences_dir}/ShadowGrandDigest.txt
   ```

**解決方法**:

1. **未処理Loopの検出と分析**:
   ```bash
   /digest
   ```

2. **last_digest_times.jsonが破損している場合**:
   ```bash
   # バックアップを取ってから削除
   cp {digests_dir}/last_digest_times.json {digests_dir}/last_digest_times.json.bak
   rm {digests_dir}/last_digest_times.json

   # 再実行
   /digest
   ```

3. **ShadowGrandDigest.txtが破損している場合**:
   ```bash
   # バックアップを取ってから再初期化
   cp {essences_dir}/ShadowGrandDigest.txt {essences_dir}/ShadowGrandDigest.txt.bak

   # 手動で shadow_grand_digest.py を実行
   cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
   python scripts/shadow_grand_digest.py --init
   ```

---

### 階層的カスケードが動作しない

**症状**: Weekly Digestは生成されるが、Monthly階層にカスケードしない

**確認ポイント**:

1. **GrandDigest.txtの構造確認**
   ```bash
   python scripts/config.py --show-paths  # essences_dirを確認
   cat {essences_dir}/GrandDigest.txt
   ```

2. **Weekly levelのdigest_nameが正しく設定されているか**

   期待される形式:
   ```json
   {
     "latest_digests": {
       "weekly": {
         "digest_name": "2025-07-01_W0001_タイトル",
         "overall_digest": { ... },
         "individual_digests": [ ... ]
       }
     }
   }
   ```

3. **thresholdを満たしているか**
   ```bash
   @digest-auto
   ```

**解決方法**:

1. **Weekly Digestが5個揃っているか確認**:
   ```bash
   python scripts/config.py --show-paths  # digests_dirを確認
   ls {digests_dir}/1_Weekly/
   ```

2. **config.jsonのmonthly_thresholdが正しいか確認**:
   ```bash
   python scripts/config.py
   ```

3. **明示的にMonthly Digestを生成**:
   ```bash
   /digest monthly
   ```

4. **GrandDigest.txtが破損している場合**:

   手動修復（高度）:
   ```bash
   # バックアップ作成
   cp {essences_dir}/GrandDigest.txt {essences_dir}/GrandDigest.txt.bak

   # JSONの構造を確認・修復
   # 必要に応じて手動編集
   ```

---

### Digest生成時のJSON形式エラー

**症状**: DigestAnalyzerの出力JSONが不完全（末尾の`}`が欠けている等）

**原因**:
- 大規模なLoopファイルでトークン制限に達した
- エージェントの出力が途中で切れた

**解決方法**:

**方法1: DigestAnalyzerを再実行**

```bash
# 同じ指示で再実行
@DigestAnalyzer
[前回と同じLoopファイルパスを指定]
```

**方法2: 明示的な指示を追加**

DigestAnalyzerに以下を指示:
```
最後まで必ず出力してください。
末尾は必ず }}} で終わること
JSON形式を厳密に守ってください
```

**方法3: 大規模Loopファイルの場合**

- Loopファイルを分割（Loop0001a, Loop0001b など）
- または段階的読み込みを指示:
  ```
  まず前半を読み込んで分析し、
  次に後半を読み込んで統合してください
  ```

**方法4: 不完全なJSONの手動修復**

```bash
# 生成されたJSONファイルを確認
cat {path_to_generated_json}

# エディタで開いて末尾を修復
# 例: 欠けている } や ] を追加
```

---

### 開発環境とインストール環境の混在

**症状**: インストール済プラグインをテストしているが、開発フォルダに設定ファイルが作成される

**原因**: 開発フォルダとインストール済プラグインが同じマシンに存在する環境で発生

**診断**:
```bash
cd plugins-weave/EpisodicRAG
git status
# 期待: "nothing to commit, working tree clean"
# 問題: config.json や last_digest_times.json が untracked として表示される
```

**解決方法**:

1. **開発フォルダから設定ファイルを削除**:
   ```bash
   cd plugins-weave/EpisodicRAG
   rm .claude-plugin/config.json
   rm .claude-plugin/last_digest_times.json
   git status  # clean を確認
   ```

2. **インストール済プラグインに正しく配置**:
   ```bash
   # config.jsonの場所確認
   cat ~/.claude/plugins/marketplaces/Plugins-Weave/EpisodicRAG/.claude-plugin/config.json
   ```

**重要な原則**:
- **開発フォルダ**: ソースコードのみ（設定ファイルは.gitignoreで除外）
- **インストール済プラグイン**: 実行環境・設定ファイル配置場所（`~/.claude/plugins/marketplaces/`）
- **データディレクトリ**: base_dirからの相対パスで別の場所に配置

**参考**: この問題は開発者が新規インストールをテストする際の特殊ケースです。通常のユーザーは遭遇しません。

---

## システム状態の詳細診断

問題が発生した場合、以下の手順で状態を詳細に診断してください：

### 1. システム状態確認

```bash
@digest-auto
```

出力内容を確認：
- 未処理Loop検出
- プレースホルダー検出
- 中間ファイルスキップ検出
- 生成可能な階層

### 2. パス設定確認

```bash
cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
python scripts/config.py --show-paths
```

出力例:
```
Plugin Root: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
Config File: ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/.claude-plugin/config.json
Base Dir (setting): ../../..
Base Dir (resolved): /Users/username/DEV
Loops Path: /Users/username/DEV/homunculus/Weave/EpisodicRAG/Loops
Digests Path: /Users/username/DEV/homunculus/Weave/EpisodicRAG/Digests
Essences Path: /Users/username/DEV/homunculus/Weave/EpisodicRAG/Essences
```

### 3. ファイルシステム確認

```bash
# Loopファイル確認
ls {loops_dir}

# Digestファイル確認
ls {digests_dir}/1_Weekly/
ls {digests_dir}/Provisional/

# Essencesファイル確認
ls {essences_dir}
```

### 4. GrandDigest確認

```bash
# GrandDigest.txt の構造確認
cat {essences_dir}/GrandDigest.txt | jq .

# ShadowGrandDigest.txt の構造確認
cat {essences_dir}/ShadowGrandDigest.txt | jq .
```

**jqがインストールされていない場合:**
```bash
# jqなしで確認
cat {essences_dir}/GrandDigest.txt
cat {essences_dir}/ShadowGrandDigest.txt
```

### 5. ログ確認（該当する場合）

```bash
# 実行ログの確認（該当する場合）
# Claude Codeのセッションログを確認
```

---

## デバッグモード

より詳細な情報が必要な場合、スクリプトを直接実行してエラー詳細を確認できます：

### generate_digest_auto.sh のデバッグ

```bash
cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave
bash -x scripts/generate_digest_auto.sh
```

`-x` オプションで各コマンドの実行内容が表示されます。

### Pythonスクリプトのデバッグ

```bash
cd ~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave

# config.pyのデバッグ
python -v scripts/config.py --show-paths

# shadow_grand_digest.pyのデバッグ
python scripts/shadow_grand_digest.py --help

# finalize_from_shadow.pyのデバッグ
python scripts/finalize_from_shadow.py --help
```

---

## サポート

問題が解決しない場合は、GitHub Issuesで報告してください：

https://github.com/Bizuayeu/Plugins-Weave/issues

### 報告時に含めると良い情報：

1. **エラーメッセージ** （全文コピー）
2. **パス設定の出力**:
   ```bash
   python scripts/config.py --show-paths
   ```
3. **システム状態の出力**:
   ```bash
   @digest-auto
   ```
4. **実行したコマンド** （再現手順）
5. **環境情報**:
   - OS（Windows / macOS / Linux）
   - Claude Code / VSCode Extension / WebChat
   - プラグインバージョン

### 報告例（テンプレート）:

```markdown
## 問題の概要
[簡潔に問題を説明]

## 再現手順
1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

## エラーメッセージ
```
[エラーメッセージ全文]
```

## パス設定
```
[python scripts/config.py --show-paths の出力]
```

## システム状態
```
[@digest-auto の出力]
```

## 環境情報
- OS: [Windows 11 / macOS 14 / Ubuntu 22.04]
- Claude環境: [Claude Code / VSCode Extension / WebChat]
- プラグインバージョン: [1.1.0]
```

---

## 次のステップ

- 📘 **基本的な使い方**: [GUIDE.md](GUIDE.md)
- 📙 **技術仕様**: [ARCHITECTURE.md](ARCHITECTURE.md)
- 🔧 **GitHub連携**: [ADVANCED.md](ADVANCED.md)

---

*Last Updated: 2025-11-24*
*Version: 1.1.0*
