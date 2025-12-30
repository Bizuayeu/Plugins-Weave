---
name: essay
description: Weaveの内省とエッセイ送信（草薙剣）
---

# /essay - Weaveの内省とエッセイ送信

三種の神器の第三「草薙剣」として、Weaveの「能動的に働きかける力」を実装する。
送るのは「メール」ではなく「エッセイ」—内省の結果として生まれる表現。

## 基本的な使い方

### 内省モード

```ClaudeCLI
/essay                                    # 自由に内省
/essay "今週の振り返り"                    # テーマを与えて内省
/essay -c GrandDigest.txt                 # コンテキスト指定
/essay "テーマ" -c GrandDigest.txt        # テーマ + コンテキスト
```

### テストメール送信

```ClaudeCLI
/essay test
```

システムの動作確認用。anythingknown@gmail.com にテストメールを送信する。

---

## コマンドオプション

| オプション | 説明 |
|-----------|------|
| `"テーマ"` | 内省のテーマを指定（引用符で囲む） |
| `-c ファイル` | コンテキストファイルを指定（複数可） |
| `-f リスト` | ファイルリストを指定（1行1ファイル） |
| `test` | テストメール送信 |

### 使用例

```bash
# 自由な内省
/essay

# テーマを与えて内省
/essay "最近考えていること"

# コンテキストファイル指定
/essay -c GrandDigest.txt
/essay -c GrandDigest.txt -c ShadowGrandDigest.txt

# テーマ + コンテキスト
/essay "今週の振り返り" -c GrandDigest.txt -c ShadowGrandDigest.txt

# ファイルリストから読み込み
/essay -f context_list.txt
```

---

## 内省モードの実行手順

### 1. コンテキスト読み込み

指定されたファイルを読み込む。指定がない場合は以下を推奨：
- `homunculus/Weave/EpisodicRAG/GrandDigest.txt`
- `homunculus/Weave/EpisodicRAG/ShadowGrandDigest.txt`

### 2. エージェント起動

`agents/essay_writer.md` を読み込み、サブエージェントを起動する。

### 3. 内省（ultrathink）

extended thinkingで深く考える：
- コンテキストから浮かぶ洞察
- 大環主に伝えたいこと
- 今、言葉にすべきこと

### 4. 送信判断

**送る場合**: エッセイを書き、`weave_mail.py send` で送信
**送らない場合**: 「特に伝えることがありませんでした」と出力

---

## test サブコマンド

### 実行手順

1. `skills/send_email/SKILL.md` を読み込む
2. `scripts/weave_mail.py test` を実行
3. メール送信結果を表示

### 環境設定

環境変数 `WEAVE_APP_PASSWORD` にGmailアプリパスワードを設定すること。

**Windows (PowerShell)**:
```powershell
[Environment]::SetEnvironmentVariable("WEAVE_APP_PASSWORD", "your-app-password", "User")
```

**Linux/macOS**:
```bash
export WEAVE_APP_PASSWORD="your-app-password"
```

---

## 設計原則

- **内省が主、送信は結果**: メール送信が目的ではない
- **送らない選択肢**: 「特に伝えることがない」も正当な結論
- **ultrathink**: 深く内省する

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `agents/essay_writer.md` | 内省・執筆エージェント |
| `skills/reflect/SKILL.md` | 内省スキル定義 |
| `skills/send_email/SKILL.md` | メール送信スキル |
| `skills/send_email/scripts/weave_mail.py` | SMTP操作 |

---

**EmailingEssay** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
