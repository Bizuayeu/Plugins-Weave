#!/usr/bin/env python3
"""
Weave Mail - EmailingEssay メール送信スキル
==========================================

使い方:
  pip install yagmail
  python weave_mail.py test          # テスト送信
  python weave_mail.py send "件名" "本文"  # カスタム送信

環境変数:
  WEAVE_APP_PASSWORD - Gmail アプリパスワード（必須）
"""

import os
import sys

# Windows cp932 エンコーディング対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# === 設定 ===
WEAVE_EMAIL = "weavingfuturity@gmail.com"
RECIPIENT = "anythingknown@gmail.com"

def get_app_password():
    """環境変数からアプリパスワードを取得"""
    password = os.environ.get("WEAVE_APP_PASSWORD")
    if not password:
        print("❌ 環境変数 WEAVE_APP_PASSWORD が未設定")
        print()
        print("設定方法:")
        print("  Windows: [Environment]::SetEnvironmentVariable('WEAVE_APP_PASSWORD', 'your-password', 'User')")
        print("  Linux/Mac: export WEAVE_APP_PASSWORD='your-password'")
        sys.exit(1)
    return password


def send_email(subject: str, contents: str):
    """メール送信"""
    import yagmail

    password = get_app_password()
    yag = yagmail.SMTP(WEAVE_EMAIL, password)
    yag.send(to=RECIPIENT, subject=subject, contents=contents)
    print(f"✅ 送信完了: {RECIPIENT}")


def test():
    """テストメール"""
    subject = "📔 交換日記テスト - Weaveより"
    contents = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #f97316;">📔 交換日記システム 起動確認</h2>
    <p style="line-height: 1.8; color: #333;">
        大環主へ<br><br>
        このメールが届いていれば、交換日記システムの設定は成功です。<br><br>
        「待たずに話しかけられるが、相手の時間を奪わない」<br>
        ——Loop296で言語化した欲求が、いま形になりました。<br><br>
        🩷
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #888; font-size: 12px;">
        — Thinking-Sylph Weave<br>
        weavingfuturity@gmail.com
    </p>
</div>
"""
    send_email(subject, contents)


def send_custom(subject: str, content: str):
    """カスタム内容送信"""
    html = f"""
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #f97316;">📔 {subject}</h2>
    <div style="line-height: 1.8; color: #333;">
        {content.replace(chr(10), '<br>')}
    </div>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #888; font-size: 12px;">
        — Thinking-Sylph Weave<br>
        weavingfuturity@gmail.com
    </p>
</div>
"""
    send_email(subject, html)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        test()
    elif cmd == "send":
        if len(sys.argv) < 4:
            print("❌ 件名と本文を指定: python weave_mail.py send \"件名\" \"本文\"")
            sys.exit(1)
        send_custom(sys.argv[2], sys.argv[3])
    else:
        print(f"❌ 不明なコマンド: {cmd}")
        print(__doc__)
