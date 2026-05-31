# claude.ai プロジェクト指示に貼る snippet

起動手順は wakeup スキルにカプセル化されるので、プロジェクト指示には **次の1行だけ**で済む：

> セッション開始時、最初に wakeup スキルを実行して長期記憶をロードしてください。

---

## token zip の作り方（Private 参照・書き戻しを使う場合のみ）

claude.ai のプロジェクトナレッジは zip 非対応のため、token は**スキル同梱の二重 zip**で持ち込む。**公開リポには token を含めない**（`.gitignore` 済み）。

1. **fine-grained PAT を発行**（対象リポ限定・最小権限）:
   - Read 用: Private リポ `Contents: Read` ＋ **Public repositories read-only**（公開リポの記憶ロードにも使う。claude.ai は共有 IP で未認証 API〔SHA 取得〕が 60req/h ですぐ枯渇し、かつ raw の main 参照は CDN キャッシュで最新が取れないため、SHA 固定取得に認証が必須）
   - Write 用: 公開リポのみ, `Contents: Read & Write` + `Pull requests: Read & Write`（**admin でない write collaborator アカウントで発行**——admin の PAT はブランチ保護を bypass するため）
2. **token を zip 化（内側）**:
   ```bash
   printf '%s' "github_pat_xxxxx" > token.txt
   zip token.zip token.txt && rm token.txt
   ```
3. `token.zip` を **スキルディレクトリ（`wakeup/`）に配置**。
4. **スキル全体を zip 化（外側）** して claude.ai にスキル登録 → 展開後 `/mnt/skills/user/wakeup/token.zip`。
5. wakeup が `extract-token --zip /mnt/skills/user/wakeup/token.zip` で読む（token は Authorization ヘッダにのみ載る）。

> スキル更新のたびに token を再注入する必要がある点に注意。本質防御は fine-grained PAT の権限最小化（zip は難読化の補助）。
