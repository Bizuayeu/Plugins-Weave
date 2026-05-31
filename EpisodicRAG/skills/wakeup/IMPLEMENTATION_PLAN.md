# Implementation Plan: wakeup スキル（claude.ai 専用セッション開始エンジン）

> 本計画は `.claude/rules/DEV.md` および `/plan-sdd` コマンドで生成。全 Stage 完了後に削除する。
> 実装は本計画の承認後に着手する（このファイルは計画のみ）。

## Overview

- **What**: EpisodicRAG プラグインに新規スキル `wakeup` を追加する。claude.ai（Computer Use）環境のセッション開始時に、(1) 公開リポから長期記憶を認証なしロード、(2) 起動ディレクティブ（人格ロード方針）を適用、(3) 表情 UI を起動、(4) 必要時に Private リポを Read PAT で動的参照、(5) 記憶を Write PAT + PR フローで書き戻す——を担う。
- **Why**: 現状の起動手順は `homunculus/Weave/Identities/HowToUseEpisodicRAG.md`（Weave 決め打ち、PAT を `grep` で stdout に晒す古い設計）に散在し、claude.ai プロジェクト指示にコピペ運用されている。これを「汎用エンジン（誰でも使える）＋ Weave 固有 config（値だけ差し替え）」に再構築し、digest-setup が `base_dir`/`threshold` を config 化したのと同じ思想で Weave 固有値を全て外出しする。あわせて PAT の stdout 露出・main 直 push といったセキュリティ負債を解消する。
- **Where**: `plugins-weave/EpisodicRAG/skills/wakeup/`（新規ディレクトリ）。Weave 固有の実値（config・起動ディレクティブ）は **プラグイン同梱の `examples/` テンプレート** とし、実運用値は claude.ai プロジェクトナレッジ側に配置（プラグイン本体に Weave 固有値を焼き込まない）。
- **Reference Patterns**:
  - `plugins-weave/ContextPreloader/`（**最重要の類似**: config(`sources.json`) 駆動で「セッション開始時に複数ソースをロードする」エンジン。Domain=Source/Settings/Config 値オブジェクト、Infrastructure=`config_repository.load_config`、依存方向 `interfaces→application→domain` を踏襲）
  - `plugins-weave/EpisodicRAG/skills/digest-setup/SKILL.md` 他 digest-* 3 種（SKILL.md 構造: frontmatter `name`/`description` → 目次 → 実装注意 → 実行フロー[TodoWrite items + Step テーブル] → 出力例。`.claude-plugin/config.template.json` の config 思想）
  - `plugins-weave/VisualExpression/skills/SKILL.md`（claude.ai bash 環境での `cp /mnt/skills/.../VisualExpressionUI.html /mnt/user-data/outputs/` + `present_files` パターン、表情キー対応表の所在）
  - `homunculus/Weave/Identities/HowToUseEpisodicRAG.md`（本スキルが置換する現行 Weave 決め打ち実装。移行元の正典）

---

## 設計の最重要前提（実装着手前に必読）

**wakeup は claude.ai のスキル bash サンドボックスで動く。Claude Code 上の Python プラグインとしては動かない。**

| 観点 | digest-*（既存） | wakeup（本スキル） |
|---|---|---|
| 実行環境 | ローカル Claude Code | claude.ai Computer Use の bash |
| 実装主体 | `python -m interfaces.digest_*`（インストール済みパッケージ） | **SKILL.md の手続き** を Claude 自身が curl/python で実行 |
| `scripts/` の import | 可（同一リポにインストール） | **不可**（claude.ai には EpisodicRAG パッケージが無い、`/mnt/skills/` に zip 展開された自スキルのみ） |
| config の所在 | `~/.claude/plugins/.episodicrag/config.json`（永続化パス） | スキル同梱 or プロジェクトナレッジ配置の `wakeup.config.json`（claude.ai に永続化ディレクトリは無い） |

この差異が Clean Architecture の層配置を規定する（下記）。「engine」とは **SKILL.md の宣言的手続き + config を読む最小ヘルパ** であり、EpisodicRAG 本体の Python 層には依存しない自己完結スクリプトとして実装する。

---

## Architecture

汎用エンジンと Weave 固有 config を分離する。依存方向は **本体（エンジン）→ config 注入**（エンジンは config の中身=Weave 値を一切ハードコードしない）。

| Layer | 本機能における責務 | 主要な型/関数/ファイル | 依存先 |
|-------|-----------------|---------------------|--------|
| **Domain** | 起動仕様の純粋表現。config の構造（リポ・ブランチ・load_files・commit_identity・directive_path）を値オブジェクト化。URL 組み立て・noreply 整形・ブランチ名生成などの純粋関数 | `WakeupConfig`, `RepoRef`(owner/name/branch/visibility), `LoadFile`(path/label/required), `CommitIdentity`(author_name/author_noreply/coauthor), `build_raw_url()`, `build_pr_branch_name()` | なし（純粋） |
| **UseCase** | 起動オーケストレーションの定義。「公開記憶ロード → ディレクティブ適用 → 表情起動」の順序と、Private 参照／書き戻しの手順契約（ports）。**ただし claude.ai 実行ぶんは SKILL.md の手続きとして表現**し、Python 側はテスト可能な純粋オーケストレーションに限定 | `BootSequence`(順序定義), ports: `MemoryLoaderPort`/`SecretProviderPort`/`VcsPort`/`FaceUiPort` | Domain のみ |
| **Interface** | config の読込・検証ゲートウェイ。claude.ai bash から呼ばれる自己完結 CLI（`wakeup_engine.py`）。SKILL.md（手続き仕様）もこの層（Driving Adapter） | `load_config(path)→WakeupConfig`, `validate_config()`, `extract_token(zip)`(stdout 非出力), `wakeup_engine.py`(`resolve-urls`/`extract-token` サブコマンド), `SKILL.md` | UseCase, Domain |
| **Infrastructure** | 外部世界。GitHub raw/API への curl、fine-grained PAT(zip)、git push/PR、`/mnt/user-data/outputs/` への表情 UI 配置、`present_files`。**大半は SKILL.md 内の bash 一行コマンドとして claude.ai が実行**（Python 常駐プロセス無し） | curl コマンド群, `python -c "import zipfile..."` 解凍, `git`/`gh`, `cp`+`present_files` | 全層（最外殻） |

### Dependency Direction

```
[Weave 固有値]                    [汎用エンジン]
examples/weave.config.json  ──注入──▶  Interface(load_config) ──▶ UseCase(BootSequence) ──▶ Domain(WakeupConfig)
examples/WeaveDirective.md  ──参照──▶  SKILL.md 手続き                                          ▲
                                                          Infrastructure(curl/git/face) ───────┘(ports 実装)
```

- **エンジンは Weave を知らない**: `wakeup_engine.py` も `SKILL.md` も、リポ名・ファイル名・noreply・ディレクティブ本文を一切ハードコードしない。全て config の値として受け取る（digest-setup が `base_dir` を持たないのと同型）。
- **config が Weave を知る**: `examples/weave.config.json` にだけ `Bizuayeu/Homunculus-Weave`・`Identities/GrandDigest.txt`・`289333046+weavingfuturity@users.noreply.github.com` 等の実値が載る。
- **directive が人格を知る**: 人格ロード方針・冷静さ維持・創発志向・表情運用は `WeaveDirective.md`（外部 md）に分離。エンジンは directive を「読んで適用せよ」と指示するだけで中身を持たない。
- **Domain は外層を import しない**: URL 組み立て・noreply 整形は純粋関数として Domain に置き、curl/git は Infrastructure（ports 経由）。

---

## Stages

> Stage 順序は内側（Domain）→外側（Infrastructure/SKILL）。各 Stage は TDD Flow（Test→Implement→Refactor→Commit）を踏む。テストは ContextPreloader の `scripts/tests/` 配置・pytest 規約に合わせる（`skills/wakeup/scripts/tests/`）。

## Stage 1: Domain — 起動仕様の値オブジェクトと純粋関数
**Goal**: config 構造を表す frozen dataclass 群と、URL/ブランチ名/noreply を組み立てる副作用ゼロの純粋関数。
**Layer**: Domain
**Success Criteria**: 外部 I/O・import なしで `WakeupConfig` を構築でき、`build_raw_url`/`build_pr_branch_name` がテストで決定的に検証できる。
**Tests** (Red → Green):
  - `build_raw_url(repo, sha, "Identities/GrandDigest.txt")` が `https://raw.githubusercontent.com/{owner}/{name}/{sha}/Identities/GrandDigest.txt` を返す（URL にトークンを載せないことを型レベルで担保）
  - `CommitIdentity` が `author_name="Weave"` と noreply を保持し、生 Gmail を渡すと `ValueError`（noreply 形式 `^\d+\+\w+@users\.noreply\.github\.com$` のみ許容）
  - `LoadFile(required=True)` と `required=False` を区別して保持する
**Implementation Notes**: ContextPreloader `domain/models.py` の frozen dataclass パターンを踏襲。`RepoRef.visibility ∈ {public, private}` で公開/非公開ロードを型で分岐。Weave 実値は **テストフィクスチャにも書かない**（汎用性検証のためダミー owner/repo を使う）。
**Status**: Not Started

## Stage 2: UseCase — BootSequence オーケストレーションと ports
**Goal**: 起動順序（公開ロード→ディレクティブ→表情）と、Private 参照／書き戻しの手順を表す ports（抽象）。Domain のみに依存。
**Layer**: UseCase
**Success Criteria**: fake adapter を注入して `BootSequence.run()` の呼び出し順序・必須ファイル欠落時の挙動をテストできる（実 curl/git を呼ばない）。
**Tests** (Red → Green):
  - `BootSequence.run()` が `MemoryLoaderPort.load_public(required_files)` → `FaceUiPort.boot()` の順で呼ばれる（fake で順序記録）
  - 必須 `LoadFile` の取得に失敗したら起動を中断しエラーを返す（任意ファイルは警告のみで継続）
  - `SecretProviderPort.with_token(scope)` がコールバック実行後にトークン参照を保持しない契約（fake が「解放された」ことを確認）
**Implementation Notes**: EmailingEssay の `usecases/ports.py` パターン（MailSender/Scheduler の抽象）を参照。ports = `MemoryLoaderPort`/`SecretProviderPort`/`VcsPort`/`FaceUiPort`。claude.ai 実行は SKILL.md が担うため、ここは「順序と契約」の SSoT に徹し過剰実装しない（YAGNI）。
**Status**: Not Started

## Stage 3: Interface — config ローダ・検証と自己完結 CLI
**Goal**: `wakeup.config.json` を読んで `WakeupConfig` に変換・検証する `load_config`、claude.ai bash から叩く `wakeup_engine.py`（`resolve-urls`・`extract-token` サブコマンド）。
**Layer**: Interface
**Success Criteria**: 不正 config で明示エラー、正常 config で SHA 解決後の raw URL 一覧を JSON 出力。`extract-token` が **トークンを stdout/stderr に一切出さず** コマンド置換 `TOKEN=$(...)` で受け取れる形にする。
**Tests** (Red → Green):
  - `load_config` が必須キー（`repos`/`load_files`/`commit_identity`/`directive_path`）欠落で `ConfigError`（ContextPreloader `ConfigError` パターン）
  - `wakeup_engine.py resolve-urls --config X --sha SHA` が load_files 分の raw URL を JSON 配列で返す
  - `extract-token` の stdout が PAT 文字列を含まない（zip からトークンを取り出すが、標準出力には出さずファイルディスクリプタ/コマンド置換専用パスへ）。**stderr にもトークンを出さない**（例外時も握りつぶしてマスクした旨のみ）
**Implementation Notes**: `wakeup_engine.py` は EpisodicRAG `scripts/` を **import しない**自己完結スクリプト（claude.ai に同梱 zip 展開される前提、`/mnt/skills/user/wakeup/...`）。標準ライブラリのみ（`json`/`zipfile`/`urllib` or curl 委譲）。digest-setup CLI の `--config '{...}'` 受け渡し規約を踏襲。
**Status**: Not Started

## Stage 4: SKILL.md + Infrastructure 手続き（claude.ai 実行フロー）
**Goal**: claude.ai が実際に辿る起動手続きを SKILL.md に宣言。curl(公開ロード)・PAT zip 解凍→単一 bash での Private 参照・Write PAT + claude/* ブランチ→PR・表情 UI 起動を Step テーブル化。
**Layer**: Interface(Driving) + Infrastructure
**Success Criteria**: digest-* と同じ SKILL.md 構造（frontmatter→目次→実装注意→実行フロー[TodoWrite+Step テーブル]→出力例）。セキュリティ規律（`-s --fail`・Authorization ヘッダ・URL 非載せ・stdout 非露出・noreply commit）が手続きに明記される。レビューで「Weave 決め打ち箇所ゼロ」を確認できる。
**Tests** (Red → Green) — *Markdown 仕様のため自動テストは限定的。検証は Stage 0 環境確認 + 手続きのドライラン*:
  - SKILL.md の curl 例が全て `-s --fail -H "Authorization: Bearer $TOKEN"` 形式で、URL にトークンを含まない（grep ベースの lint チェック 1 本を tests に追加）
  - SKILL.md・wakeup_engine.py に Weave 固有文字列（`Bizuayeu`/`weavingfuturity`/`Homunculus`）が出現しない（lint チェック、実値は examples/ のみ許可）
  - 書き込み手続きが `git push origin claude/*` → PR 作成で、`main` への直 push コマンドを含まない
**Implementation Notes**:
  - **公開ロード**: config の `repos.public` + `load_files` を SHA 解決後に認証なし curl。VisualExpression と違い PAT 不要。
  - **Private 参照（on-demand）**: `TOKEN=$(python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py extract-token --zip /mnt/skills/user/wakeup/token.zip) && curl -s --fail -H "Authorization: Bearer $TOKEN" <api-url>` を **単一 bash 呼び出し**で完結（トークン常駐回避、token はスキル同梱の内側 zip）。
  - **書き戻し**: Write PAT で `claude/<topic>` ブランチ push → `gh pr create`。commit author=config の `commit_identity`（Weave noreply）、co-author=`Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。WeaveIdentity 等人格核(Domain層)への書込は「PR 必須・要熟慮」と手続き上で区別（WORKLOG/IntentionPad は記録系として通常フロー）。
  - **commit identity 設定**: 対象リポの local `git config user.name/user.email` のみ設定（global の Bizuayeu は不変、他リポ非影響）と手続きに明記。
  - **表情**: VisualExpression へ委譲。`cp /mnt/skills/user/visual-expression/VisualExpressionUI.html /mnt/user-data/outputs/` + `present_files` の**起動トリガーのみ** wakeup が持ち、表情キー対応表は重複させず VisualExpression SKILL.md を参照。
  - **examples/**: `examples/weave.config.json`（実値）+ `examples/WeaveDirective.md`（HowToUseEpisodicRAG.md の「人格ロード方針」「表情運用」を移植）+ `examples/PROJECT_INSTRUCTIONS_snippet.md`（claude.ai プロジェクト指示に貼る「最初に wakeup を実行」1 行）+ zip 作成手順ドキュメント。
**Status**: Not Started

## Stage 0: 環境前提の検証（Stage 1 着手前に実施）
**Goal**: claude.ai スキル bash 環境で declared deps のみで再現するか確認。
**Layer**: —（環境検証）
**Success Criteria**: 以下 3 点を claude.ai 実機で確認しメモ化:
  - (a) 外部ネットワーク curl 可（GitHub raw/API へ HTTP 200。HowToUse で実証済みだが念のため再確認）
  - (b) `python3` + `zipfile` で zip 解凍可（標準ライブラリのみ、追加 pip 不要を確認）
  - (c) `present_files` 利用可（`/mnt/user-data/outputs/` への配置→サイドバー表示）
**Implementation Notes**: MEMORY.md「完了報告の環境依存チェック」に従い、開発機の偶然の状態に依存しないことを確認。失敗時は 3-Strike Rule で代替（curl→python urllib、present_files 不可時は Artifact 表示）を検討。
**Status**: Not Started

---

## Documentation Plan

### 基本セット（毎回確認）

| ドキュメント | パス | 新規 / 更新 / 不要 | 計画内容 / 理由 |
|---|---|---|---|
| `README.md` | `plugins-weave/EpisodicRAG/README.md` | 更新 | 「セッション間で記憶を引き継ぐ」節と「主なコマンド」表に `@wakeup`（claude.ai 起動）を追記。ADVANCED.md の claude.ai 起動部分から wakeup へ誘導 |
| `CHANGELOG.md` | `plugins-weave/EpisodicRAG/CHANGELOG.md` | 更新 | 次マイナー（v5.5.0）に「Added: wakeup skill（claude.ai セッション開始エンジン、公開記憶ロード＋Private Read PAT＋Write PR フロー＋表情起動、Weave 固有値は examples/ に外出し）」を追加 |
| `IMPLEMENTATION_PLAN.md` | `plugins-weave/EpisodicRAG/skills/wakeup/IMPLEMENTATION_PLAN.md` | 新規（本書） | 全 Stage 完了後に削除 |

### 拡張レイヤー（直接調査結果 — 本環境に Explore サブエージェント tool が無いため main で実施）

| ドキュメント | パス | 候補 | 1行根拠 |
|---|---|---|---|
| `skills/wakeup/SKILL.md` | `plugins-weave/EpisodicRAG/skills/wakeup/SKILL.md` | 新規 | スキル本体仕様。Stage 4 の成果物そのもの |
| `examples/WeaveDirective.md` | `skills/wakeup/examples/WeaveDirective.md` | 新規 | 起動ディレクティブ（人格ロード方針・表情運用）。HowToUseEpisodicRAG.md からの移行先 |
| `examples/weave.config.json` | `skills/wakeup/examples/weave.config.json` | 新規 | Weave 用 config 実値（config.template.json と同型のサンプル） |
| `examples/PROJECT_INSTRUCTIONS_snippet.md` | `skills/wakeup/examples/` | 新規 | claude.ai プロジェクト指示に貼る「最初に wakeup を実行」1 行＋zip 配置手順 |
| `HowToUseEpisodicRAG.md` | `homunculus/Weave/Identities/HowToUseEpisodicRAG.md` | **廃止（ポインタ化）** | SSoT 違反解消。内容は `examples/WeaveDirective.md`（人格・表情）と SKILL.md（起動手続き）へ移行。移行後は本ファイルを wakeup へのポインタ 1 行に縮小 or 削除。**移行完了をもって削除可否をユーザー確認**（STRUCTURE.md / WeaveSupplement.md が参照しているため、参照先の張り替えが必要） |
| `docs/user/ADVANCED.md` | `plugins-weave/EpisodicRAG/docs/user/ADVANCED.md` | 更新 | 既存「GitHubセットアップ／WebChatの場合」が手動 curl + SHA コピペを案内。wakeup スキル経由へ誘導し、PAT を stdout に出す旧手順との重複を解消（片方をポインタ化） |
| `homunculus/Weave/STRUCTURE.md` | `homunculus/Weave/STRUCTURE.md` | 更新（参照張替） | HowToUseEpisodicRAG.md 参照を wakeup/examples へ更新 |
| `homunculus/Weave/Identities/WeaveSupplement.md` | 同左 | 更新（参照張替） | 起動手順の所在を wakeup スキルへ更新（記憶アーキテクチャ節） |
| `plugins-weave/README.md` | `plugins-weave/README.md` | 更新（小） | プラグイン一覧の EpisodicRAG 説明に claude.ai 起動対応を一言追記（任意） |
| `skills/shared/_implementation-notes.md` | `plugins-weave/EpisodicRAG/skills/shared/_implementation-notes.md` | 更新（小） | claude.ai 環境スキルのセキュリティ規律（PAT stdout 非露出・curl `-s --fail`・noreply commit）を共通ガイドラインとして追記。digest-* と wakeup で SSoT 化 |
| `GLOSSARY.md` | `plugins-weave/EpisodicRAG/GLOSSARY.md` | 更新（小） | 「コマンド・スキル」表に `@wakeup` を追加。新用語（起動ディレクティブ／Read PAT／Write PR フロー）を定義 |

#### 判定の原則メモ
- **SSoT 違反の中心は HowToUseEpisodicRAG.md と ADVANCED.md**。両者が「セッション開始時の curl 手順」を別々に持つ。wakeup を唯一の正典とし、両者はポインタ化（HowToUse は人格部分のみ examples へ移植）。
- HowToUseEpisodicRAG.md の**削除は参照張替（STRUCTURE.md / WeaveSupplement.md）完了後**。迷うので「廃止候補」に倒し、実削除はユーザー承認後。
- 新規ドキュメントは `skills/wakeup/` 配下に集約（既存に居場所が無い claude.ai 起動仕様のため正当）。
- 実作成は実装完了時にユーザー承認を得てから。表に並べるのは「確認」のため。

---

## 前提条件（大環主の GitHub 手作業 — 実装前に完了が必要）

エンジン実装と独立して、以下の GitHub 側設定をユーザー（大環主）が手動で行う必要がある。計画に明記し、Stage 着手の依存として扱う。

1. **fine-grained PAT ×2 発行**:
   - Read 用: `Homunculus-Weave-Private` 限定, `Contents:Read` のみ（Private Loop/Wiki 参照用）
   - Write 用: `Homunculus-Weave` 限定, `Contents:Read&Write` + `Pull requests:Read&Write`（記憶書き戻し用）
2. **`Homunculus-Weave` の main ブランチ保護**: `Require a pull request before merging` + `Do not allow bypassing the above settings`（PAT 漏洩時も main を防御）。
3. **`weavingfuturity` を collaborator 追加**（contribution graph=grass 用。commit author を weavingfuturity noreply にしても、push は Bizuayeu のため、grass を weavingfuturity に紐付けるなら collaborator 化が要る）。
4. **`weavingfuturity` で email privacy 有効化**（`Keep my email addresses private`。noreply `289333046+weavingfuturity@users.noreply.github.com` を有効化）。
5. **token の配送（二重 zip 方式 — 2026-05-31 変更）**: claude.ai のプロジェクトナレッジは **zip 非対応**と判明したため、token は**スキル同梱**で持ち込む。token を zip 化（内側 `token.zip`）→ スキルディレクトリに配置 → スキル全体を zip 化（外側）→ claude.ai にスキル登録。展開後 `/mnt/skills/user/wakeup/token.zip` を `extract_token_from_zip` で読む（**Stage 3 実装をそのまま流用、変更不要**）。公開リポには `token.zip` を含めない（`.gitignore` で除外）。難読化目的、本質防御は依然 fine-grained 権限最小化。手順は Stage 4 の examples で提供。
   - *廃案*: 「Read/Write PAT を `/mnt/project/` に配置」案は、プロジェクトナレッジが zip 非対応のため不成立。

> commit identity 三層分離の確認: push 認証=Bizuayeu（責任主体・現状の gh auth/credential manager 不変）／ commit author=Weave noreply（記憶の書き手、対象リポの local git config のみ設定）／ co-author=Claude Opus 4.8 (1M context)（基盤実体、既存慣習）。

---

## 検証済み事実（前提、再検証不要）

- `Bizuayeu/Homunculus-Weave` は Public（`private:false`）。raw も API も認証なし HTTP 200。未認証レート 60req/h、1 セッション 1 回なので余裕 → **公開ロードに PAT 不要**（Stage 4 設計の根拠）。
- `weavingfuturity` 実在（id:289333046, name:Weave, 2026-05-31 作成）。noreply: `289333046+weavingfuturity@users.noreply.github.com`（Stage 1 の CommitIdentity 実値）。
- 既存 digest-setup/digest-auto はローカル Claude Code 用・Python CLI 主体。SKILL.md 構造・`shared/_implementation-notes.md` 共通ガイドライン・GLOSSARY.md 参照の慣習を踏襲する。

---

## Decision Priority Notes

DEV.md 優先順位（Testability > Readability > Consistency > Simplicity > Reversibility）の本計画への適用と分岐記録:

- **Testability vs Simplicity（最大の分岐）**: claude.ai 実行ぶんは「SKILL.md の Markdown 手続き」で完結させれば Python は最小で済む（Simplicity）。だが純粋ロジック（URL 組み立て・noreply 検証・config 検証）を Domain/Interface の Python に切り出すことで自動テスト可能にした（Testability 優先）。SKILL.md の手続き自体は lint チェック（Weave 固有文字列・URL トークン混入・main 直 push 検出）で最低限担保。
- **Consistency**: config 思想は `config.template.json`、層配置・テスト規約は ContextPreloader、SKILL.md 構造は digest-* に合わせ、独自設計を避けた。
- **Reversibility**: 汎用エンジンと Weave 値（examples/）を分離したため、別ユーザーへの転用も Weave 値の差し替えも config 編集だけで済む（digest-setup の base_dir 外出しと同型）。HowToUseEpisodicRAG.md は即削除せずポインタ化で巻き戻し余地を残す。
- **YAGNI 解除対象の明示**: Stage 3 の「トークン stdout/stderr 非露出」テスト、Stage 4 の lint チェックは YAGNI 対象外（セキュリティ契約の明示化＝基底要件）。一方、複数ユーザー config 切替や Read/Write 以外の PAT スコープは将来要件として今は入れない（YAGNI）。

---

## 3-Strike Rule

本機能で 3 回詰まった場合の停止条件:

- **詰まりやすい予想ポイント**:
  1. claude.ai bash でのトークン非露出（コマンド置換 `TOKEN=$(...)` がツール結果に残らないか／python の例外時 stderr 漏れ）
  2. `present_files` / `/mnt/user-data/outputs/` の実挙動が VisualExpression 前提と一致するか（Stage 0 で先行検証）
  3. commit author（Weave noreply）と push 認証（Bizuayeu）の分離が grass/PR 上で意図通り反映されるか
- **代替アプローチ候補**:
  1. zip 解凍を python から `unzip` コマンド + `--fail` 握り潰しへ／トークンを環境変数経由でなく一時 FD へ
  2. `present_files` 不可なら Artifact 直接表示にフォールバック
  3. grass が付かない場合 collaborator 設定 or author/committer の組み合わせを再検討（前提条件 3 に依存）
- **ユーザーへ相談する判断ライン**: Stage 0 で (a)(b)(c) のいずれかが claude.ai 実機で再現しない／前提条件の GitHub 手作業（PAT 発行・ブランチ保護）が未完で実装検証が進められない／トークン非露出を 3 手で担保できない場合は、`AskUserQuestion` で方針（環境差吸収 vs スコープ縮小）を仰ぐ。
