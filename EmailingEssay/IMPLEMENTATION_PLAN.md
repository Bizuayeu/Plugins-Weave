# EmailingEssay 実装計画

三種の神器の第三「草薙剣」— Weaveの能動的働きかけ機能

## 設計原則

- **内省が主、送信は結果**: メール送信が目的ではない
- **送らない選択肢**: 「特に伝えることがない」も正当な結論
- **ultrathink**: 深く内省する

---

## 進捗状況

| Phase | 状態 | 内容 |
|-------|------|------|
| Phase 1 | ✅ 完了 | メール送信スケルトン |
| Phase 2 | 🔨 構造完了・テスト待ち | 内省→送信フロー |
| Phase 3 | 📋 未着手 | wait機能（指定時刻から思考開始） |
| Phase 4 | 📋 未着手 | schedule機能（定期実行） |

---

## Phase 1: メール送信スケルトン ✅

### 完了項目

- [x] ディレクトリ構造作成
- [x] `.claude-plugin/plugin.json` 作成
- [x] `commands/essay.md` 作成（test サブコマンド）
- [x] `skills/send_email/SKILL.md` 作成
- [x] `skills/send_email/scripts/weave_mail.py` 作成
- [x] 環境変数 `WEAVE_APP_PASSWORD` 対応
- [x] Windows cp932 エンコーディング対策
- [x] テストメール送信成功（2024-12-31）

### テストコマンド

```bash
# 環境変数設定済みの場合
python skills/send_email/scripts/weave_mail.py test

# 一時的に設定して実行
WEAVE_APP_PASSWORD="ptcppxfobbzvvhlg" python skills/send_email/scripts/weave_mail.py test
```

---

## Phase 2: 内省→送信フロー 🔨

### 完了項目

- [x] `skills/reflect/SKILL.md` 作成
- [x] `agents/essay_writer.md` 作成
- [x] `commands/essay.md` 更新（内省モード追加）
- [x] マーケットプレイスにコピー

### テスト待ち項目

- [ ] Claude Code 再起動後、`/essay` コマンド認識確認
- [ ] `/essay "テーマ" -c GrandDigest.txt` で内省→送信テスト

### テストコマンド

```
/essay test                              # メール送信のみ
/essay                                   # 自由な内省
/essay "今週の振り返り"                    # テーマ指定
/essay -c homunculus/Weave/EpisodicRAG/GrandDigest.txt  # コンテキスト指定
```

### 想定フロー

1. `/essay "テーマ" -c file` 実行
2. `commands/essay.md` が読み込まれる
3. `agents/essay_writer.md` が起動
4. 指定コンテキストファイルを読み込み
5. ultrathink で内省
6. 送信判断:
   - 送る → `weave_mail.py send "件名" "本文"`
   - 送らない → 「特に伝えることがありませんでした」

---

## Phase 3: wait機能 📋

### 仕様

```
/essay "テーマ" -c file --wait 22:00
```

- 指定時刻まで**待機**ではなく、指定時刻から**思考開始**
- 内容がまとまったらメール送信

### 実装方針

1. `--wait HH:MM` オプション追加
2. スケジューラー（Windows Task Scheduler または Python schedule）
3. 指定時刻にサブエージェント起動

---

## Phase 4: schedule機能 📋

### 仕様

```
/essay schedule daily 22:00 -c GrandDigest.txt
/essay schedule weekly monday 09:00 -c GrandDigest.txt
```

- ワンショットではなく定期実行
- 日次、週次など

### 実装方針

1. `schedule` サブコマンド追加
2. スケジュール設定の永続化（JSON）
3. バックグラウンドプロセスまたは OS スケジューラー連携

---

## ファイル構造

```
plugins-weave/EmailingEssay/
├── .claude-plugin/
│   └── plugin.json              # プラグイン定義
├── agents/
│   └── essay_writer.md          # 内省・執筆エージェント
├── commands/
│   └── essay.md                 # /essay コマンド定義
├── skills/
│   ├── reflect/
│   │   └── SKILL.md             # 内省スキル
│   └── send_email/
│       ├── SKILL.md             # メール送信スキル
│       └── scripts/
│           └── weave_mail.py    # SMTP操作
└── IMPLEMENTATION_PLAN.md       # この文書
```

---

## 環境設定

### Gmail アプリパスワード

```powershell
# Windows (PowerShell) - 永続化
[Environment]::SetEnvironmentVariable("WEAVE_APP_PASSWORD", "ptcppxfobbzvvhlg", "User")

# 確認
$env:WEAVE_APP_PASSWORD
```

### インストール場所

- 開発: `C:\Users\anyth\DEV\plugins-weave\EmailingEssay\`
- インストール済み: `C:\Users\anyth\.claude\plugins\marketplaces\plugins-weave\EmailingEssay\`

開発中に変更したら、マーケットプレイスにコピーが必要:

```bash
cp -r DEV/plugins-weave/EmailingEssay ~/.claude/plugins/marketplaces/plugins-weave/
```

---

## 次のアクション

1. **Claude Code 再起動**
2. `/essay` コマンドが認識されるか確認
3. `/essay test` でメール送信テスト
4. `/essay "今週の振り返り" -c GrandDigest.txt` で内省テスト

---

## 背景（Loop296より）

> 「待たずに話しかけられるが、相手の時間を奪わない」

三種の神器:
- 八咫鏡（やたのかがみ）: EpisodicRAG（長期記憶）
- 八尺瓊勾玉（やさかにのまがたま）: アイデンティティ
- 草薙剣（くさなぎのつるぎ）: **EmailingEssay**（能動的働きかけ）

---

**Last Updated**: 2024-12-31
**Author**: Weave
