---
name: send_email
description: メール送信スキル（Gmail SMTP + Yagmail）
---

# send_email - メール送信スキル

Gmail SMTP を使用してメールを送信するスキル。
frugal な設計で、依存は yagmail のみ。

## 設定

### 環境変数

| 変数名 | 説明 |
|--------|------|
| `WEAVE_APP_PASSWORD` | Gmail アプリパスワード（必須） |

### 送信元/送信先

| 項目 | 値 |
|------|-----|
| 送信元 | weavingfuturity@gmail.com |
| 送信先 | anythingknown@gmail.com |

---

## 使い方

### テストメール送信

```bash
cd plugins-weave/EmailingEssay/skills/send_email/scripts
python weave_mail.py test
```

### カスタム内容送信

```bash
python weave_mail.py send "件名" "本文"
```

---

## 実装詳細

### スクリプトパス

```
skills/send_email/scripts/weave_mail.py
```

### 依存関係

```
yagmail
```

### セキュリティ

- APP_PASSWORD は環境変数から取得（ハードコード禁止）
- Gmail 2FA 環境ではアプリパスワードを使用

---

## トラブルシューティング

### 環境変数未設定エラー

```
環境変数 WEAVE_APP_PASSWORD が未設定
```

**解決方法**:
```powershell
# Windows
[Environment]::SetEnvironmentVariable("WEAVE_APP_PASSWORD", "your-password", "User")
# PowerShell再起動後に反映
```

### 認証エラー

Gmail の設定で「安全性の低いアプリのアクセス」が無効の場合、
2FA を有効にしてアプリパスワードを生成してください。

---

**EmailingEssay** by Weave
