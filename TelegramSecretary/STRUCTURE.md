# STRUCTURE: TelegramSecretary の構造地図

「どこに何を置くか」の正典。設計の why は [DESIGN.md](./DESIGN.md)。

## プレースホルダ規約

配布物のドキュメント・テンプレートで使う山括弧トークンは、利用者が自分の値へ置換する：

| プレースホルダ | 意味 | 例 |
|---|---|---|
| `<AGENT_NAME>` | 秘書エージェントの人格名 | あなたの AI 秘書の呼称 |
| `<OWNER>` | 運用主体（principal） | あなた自身 |
| `<ORGANIZATION>` | 組織名 | 所属企業・チーム |
| `<REPO_ROOT>` | リポジトリルート | クローン先のルート |
| `<BASE_REPO>` | 基本設定リポ名（Cloud Routine が cwd 親に並列 clone する基本設定リポ。`schedule` が `sources` から実値置換） | `Homunculus-Weave` |
| `<PRIVATE_DIR>` | 非公開データ・人格定義の配置先（Cloud Routine では cwd 親起点の相対） | `Homunculus-Weave-Private/TelegramSecretary` |
| `<INSTALL_DIR>` | インストール先パス | TelegramSecretary 配置先 |
| `<state_dir>` | 運用 state の保存先 | env `TELEGRAM_SECRETARY_STATE_DIR` |

`SecretaryRole` はロール名として汎用使用（置換不要）。人格の実体定義は `<PRIVATE_DIR>/Identities/SecretaryRole.md`、雛型は [`templates/SecretaryRole.template.md`](./templates/SecretaryRole.template.md)。

**運用設定は config.json に集約**: `agent_name` / `private_dir` / `session_duration_sec` は手置換せず `<INSTALL_DIR>/config.json`（`.gitignore` 除外、雛型 `templates/config.template.json`、`init-config` 生成）に置く。ROUTINE_PROMPT は Step 0 でこれを読み、`<INSTALL_DIR>` / `<REPO_ROOT>` は bootstrap が env 解決する（運用値の手置換は不要）。秘匿（bot token / authorized chats）は env、非秘匿の運用設定は config.json が単一正典（**純2層**）。

## 全体像（3区分）

| 区分 | git | 中身 |
|---|---|---|
| **public（配布物）** | marketplace プラグインとして公開 | scripts（コード）・ドキュメント・テンプレート（雛型） |
| **Private（実体）** | 別の非公開リポ（`<PRIVATE_DIR>`） | 人格実体・管理表実データ・運用 state |
| **除外（開発専用・実体）** | `.gitignore` | 開発専用ディレクトリ（`docs/devlog/`・`LineBridge/`）・生成物・`state/`・`config.json`（運用設定の実体。雛型 `templates/config.template.json` は配布対象） |

**鉄則**: public には個人情報・人格を一切焼き込まない。実体はすべて Private。これが配布可能性の担保。

## public ツリー（`<INSTALL_DIR>/`）

```
TelegramSecretary/
├── .claude-plugin/
│   └── plugin.json           # marketplace マニフェスト（name/version/keywords）
├── README.md                 # 入口インデックス
├── DESIGN.md                 # 設計正典（why）
├── STRUCTURE.md              # 本ファイル（where）
├── SECURITY.md               # 網羅的セキュリティ正典
├── ROUTINE_PROMPT.md         # Cloud Routine prompt body
├── CHANGELOG.md              # 変更履歴
├── bootstrap.sh
├── pyproject.toml
├── .gitignore
│
├── commands/
│   └── telegram-secretary.md # /telegram-secretary 管理パネル入口
│
├── skills/
│   └── telegram-secretary/
│       └── SKILL.md          # スキルマニフェスト（仕様 SSoT）
│
├── templates/                # 雛型のみ（実データは Private）
│   ├── config.template.json   # 運用設定の雛型（実体は <INSTALL_DIR>/config.json、.gitignore）
│   ├── env.example            # 環境変数の雛型
│   ├── INDIVIDUALS.template.json
│   ├── TASKS.template.json
│   ├── KNOWLEDGE.template.json
│   └── SecretaryRole.template.md
│
├── scripts/                  # Clean Architecture 4層
│   ├── main.py               # CLI entrypoint（subcommands）
│   ├── domain/               # 純粋ロジック・値オブジェクト
│   │   ├── models.py / media.py / outbound.py / exceptions.py
│   │   ├── authorization.py / lease.py / normalize.py / offset.py / watch_window.py
│   │   └── registry.py       # 管理表 値オブジェクト（Individual / Identity / Task / Knowledge）
│   ├── usecases/             # オーケストレーション + Port
│   │   ├── ports.py          # Port 定義（Store 群含む）
│   │   ├── acquire_lease.py / renew_lease.py / release_lease.py
│   │   ├── fetch_authorized_updates.py / send_reply.py
│   │   ├── download_authorized_media.py / render_authorized_media.py
│   │   └── manage_registry.py # 管理表 CRUD UseCase
│   ├── adapters/
│   │   ├── media_failure.py  # render/transcribe 共通の失敗ログ + redact ヘルパ
│   │   ├── telegram/         # api_gateway / media_downloader
│   │   ├── state/            # json_state_store / emitter
│   │   ├── render/ transcribe/ audio/   # markitdown / pdf / moonshine / ffmpeg
│   │   └── registry/         # json_registry_store
│   ├── infrastructure/
│   │   ├── config.py / media_cleanup.py
│   │   ├── composition.py    # Composition Root（load_config / build_media_stack）
│   │   ├── exit_codes.py     # 終了コード（0/1/2/3/4）の SSoT
│   │   ├── registry_cli.py   # 管理表 CRUD の CLI 配線
│   │   └── archive_rotate.py # 日付Archive（TASKS/INDIVIDUALS）+ カテゴリ分割（KNOWLEDGE）
│   └── tests/                # 全層のテスト（配布物として公開）
│
└── （docs/devlog/・LineBridge/ は .gitignore 除外＝開発リポのみ、配布物には含まれない）
```

## Private ツリー（`<PRIVATE_DIR>` 配下）

```
<Private root>/
├── Identities/                       # 人格定義（無いと人格的に振る舞えない）
│   └── SecretaryRole.md              # SecretaryRole の存在論・対応原則（人格定義）
│
└── <TELEGRAM_SECRETARY_STATE_DIR>/   # 運用 state + 管理表実データ
    ├── README.md                     # 蓄積データのユーザ用インデックス（生成物）
    ├── offset.json / lease.json      # 既存 state
    ├── media/                        # 受信メディア（retention で自動削除）
    ├── individuals/
    │   ├── INDIVIDUALS.json           # 現役（SSoT）
    │   └── archive/INDIVIDUALS_<YYYY-MM>.json
    ├── tasks/
    │   ├── TASKS.json
    │   └── archive/TASKS_<YYYY-MM>.json
    └── knowledge/
        ├── KNOWLEDGE.json             # 小規模時は単一
        ├── <category>.json            # 肥大化時はカテゴリ分割（archive せず蓄積）
        └── archive/                   # （原則空。明示的廃棄時のみ）
```

> `Identities/` と `<state_dir>/` の `<PRIVATE_DIR>` 内の正確な親パスは、利用者が自分の非公開リポ構成に合わせて決定する。env `TELEGRAM_SECRETARY_STATE_DIR` で state_dir を指す。

## どこに何を作るか（早見表）

| 作るもの | 配置 | 区分 |
|---|---|---|
| 運用設定 config.json | `<INSTALL_DIR>/config.json`（`.gitignore`） | 実体（除外） |
| 関係者データ INDIVIDUALS.json | `<state_dir>/individuals/` | Private |
| 依頼データ TASKS.json | `<state_dir>/tasks/` | Private |
| 対応知 KNOWLEDGE.json（→category 分割） | `<state_dir>/knowledge/` | Private |
| 秘書人格 SecretaryRole.md | `<Private>/Identities/` | Private |
| 各管理表・秘書人格の雛型 | `templates/` | public |
| 管理表の値オブジェクト | `scripts/domain/registry.py` | public |
| 管理表 CRUD ロジック | `scripts/usecases/manage_registry.py` + Port | public |
| 管理表の JSON 永続化 | `scripts/adapters/registry/json_registry_store.py` | public |
| Archive / カテゴリ分割 | `scripts/infrastructure/archive_rotate.py` | public |

## データフロー

```
[起動] bootstrap → エージェント人格ロード（本体 Identity / Instruction / UserIdentity）
                 → Identities/SecretaryRole.md を重ねる（SecretaryRole 起動）
                 → lease acquire → watch 起動

[受信] Telegram → fetch → 認可 → 正規化 → media download/render → emit(JSON Lines)
        → エージェント（SecretaryRole）が読む

[判断] エージェントが文脈で判断（重要度の世界）:
        - 関係者を INDIVIDUALS に登録/更新すべきか
        - 依頼を TASKS に起票/進捗更新すべきか
        - 対応知を KNOWLEDGE に残すべきか
        → 該当する CLI subcommand を呼ぶ（決定論 I/O）

[応答] エージェント起草 → 出力漏洩スキャン → send-reply（必要なら --file/--reply-to）

[保守] archive_rotate: TASKS/INDIVIDUALS は日付 Archive、KNOWLEDGE は category 分割
        state README を再生成（件数・最終更新・分割状況）
```

## `/telegram-secretary` ラップ（操作の入口）

管理表 CRUD の全インターフェース（`individuals|tasks|knowledge list|get|add|remove`）は、マスタースキル `/telegram-secretary` の管理パネル経由でアクセスできる。エージェントも人間ユーザーも、コマンド名を覚えずに `/telegram-secretary` から操作に到達する。
