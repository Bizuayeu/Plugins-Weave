# claude.ai プロジェクト指示に貼る snippet

起動手順は wakeup スキルにカプセル化されるので、プロジェクト指示には **次の1行だけ**で済む：

> セッション開始時、最初に wakeup スキルを実行して長期記憶をロードしてください。

---

## token アーカイブの作り方（記憶ロード・Private 参照・書き戻しに必須）

claude.ai のプロジェクトナレッジは zip 非対応、かつスキル zip は**ネスト zip を許さない**。token は **tar.gz でスキルに同梱**する（バイナリなのでコンテキストに自動展開されない）。**公開リポには token を含めない**（`.gitignore` 済み）。engine は tar.gz / tgz / tar / gz / zip を全部読める。

1. **fine-grained PAT を発行**（対象リポ限定・最小権限）:
   - Read 用: Private リポ `Contents: Read` ＋ **Public repositories read-only**（公開リポの記憶ロードにも使う。claude.ai は共有 IP で未認証 API〔SHA 取得〕が 60req/h ですぐ枯渇し、raw の main は CDN キャッシュで最新が取れないため、SHA 固定取得に認証が必須）
   - Write 用: 公開リポのみ, `Contents: Read & Write` + `Pull requests: Read & Write`（**admin でない write collaborator アカウントで発行**——admin の PAT はブランチ保護を bypass するため）
2. **token を tar.gz 化**:
   ```bash
   printf '%s' "github_pat_xxxxx" > token.txt
   tar czf token.tar.gz token.txt && rm token.txt
   ```
3. `token.tar.gz` を **スキルディレクトリ（`wakeup/`）に配置**（Read 用と Write 用で分けるなら `token-read.tar.gz` / `token-write.tar.gz` 等）。
4. **スキル全体を zip 化** して claude.ai にスキル登録 → 展開後 `/mnt/skills/user/wakeup/token.tar.gz`。
5. wakeup が `extract-token --archive /mnt/skills/user/wakeup/token.tar.gz` で読む（token は Authorization ヘッダにのみ載る）。

> スキル更新のたびに token を再注入する必要がある点に注意。本質防御は fine-grained PAT の権限最小化（tar.gz は難読化＋コンテキスト回避の補助）。
