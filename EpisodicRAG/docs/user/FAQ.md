[Docs](../README.md) > FAQ

# よくある質問 (FAQ)

EpisodicRAGプラグインに関するよくある質問と回答集です。

## 目次

- [一般的な質問](#一般的な質問)
- [導入・セットアップ](#導入セットアップ)
- [日常的な使い方](#日常的な使い方)
- [トラブルシューティング](#トラブルシューティング)
- [開発者向け](#開発者向け)
- [関連ドキュメント](#関連ドキュメント)

---

## 一般的な質問

### Q: EpisodicRAGとは何ですか？

**A**: EpisodicRAGは、AI（Claude）との会話履歴を階層的に構造化・保存し、セッション間で記憶を引き継ぐためのプラグインです。8階層（Weekly〜Centurial、約108年分）の記憶構造で、長期的な知識管理を実現します。

### Q: 無料で使えますか？

**A**: はい、個人・非商用利用はMITライセンスの範囲で自由に利用できます。商用利用については、特許権（特願2025-198943）との関係で事前相談が必要です。

### Q: どのAI環境で動作しますか？

**A**: 以下の環境で動作します：
- Claude Code（CLI）
- Claude VSCode Extension
- Claude WebChat（一部機能制限あり）

---

## 導入・セットアップ

### Q: インストールに失敗します

**A**: 以下を確認してください：

1. マーケットプレイスが追加されているか
   ```bash
   /marketplace list
   ```

2. 正しいプラグイン名でインストールしているか
   ```bash
   /plugin install EpisodicRAG-Plugin@Plugins-Weave
   ```

3. ネットワーク接続に問題がないか

### Q: 設定ファイルが見つかりません

**A**: `@digest-setup`を実行して初期セットアップを完了してください。設定ファイルは自動的に作成されます。

```bash
@digest-setup
```

### Q: パスが正しく解決されません

**A**: `@digest-config`で設定を確認・修正してください：

```bash
@digest-config
```

`base_dir`の設定が正しいか確認してください。デフォルト（`.`）はプラグインルート自身を指します。

> 📖 パス設定の詳細は [GLOSSARY.md](../GLOSSARY.md#基本概念) および [API_REFERENCE.md](../dev/API_REFERENCE.md#config.json-詳細仕様) を参照してください。

---

## 日常的な使い方

### Q: Loopファイルの命名規則は？

**A**: `Loop[連番]_[タイトル].txt` の形式です。

**例**: `Loop0001_認知アーキテクチャ論.txt`

> 📖 詳細（正規表現・連番ルール）は [GLOSSARY.md > ファイル命名規則](../GLOSSARY.md#ファイル命名規則) を参照

### Q: `/digest`と`/digest weekly`の違いは？

**A**:
- **`/digest`**: Loopを追加したら都度実行（記憶定着）
- **`/digest weekly`**: 5個溜まったら実行（確定）

> 📖 実行フロー・データフローの詳細は [GUIDE.md > コマンド詳解](GUIDE.md#digest-コマンド) を参照

### Q: まだらボケとは何ですか？

**A**: AIがLoopの内容を記憶できていない状態です。`Loop追加 → /digest`のサイクルで予防できます。

> 📖 **SSoT**: 発生パターン・対策・記憶定着サイクルの詳細は [_common-concepts.md](../../skills/shared/_common-concepts.md#まだらボケとは) を参照

### Q: threshold（閾値）を変更したい

**A**: `@digest-config`で対話的に変更できます：

```bash
@digest-config
→ [4] Thresholds（生成条件）を選択
```

> 📖 Thresholdの詳細は [API_REFERENCE.md](../dev/API_REFERENCE.md#config.json-詳細仕様) を参照してください。

---

## トラブルシューティング

問題が発生した場合は、以下のドキュメントを参照してください：

| 症状 | 参照先 |
|------|--------|
| DigestAnalyzerが起動しない | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#digestanalyzerエージェントが起動しない) |
| individual_digestsが空になる | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#individual_digestsが空になる) |
| ShadowGrandDigestが更新されない | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#shadowgranddigestが更新されない) |
| 階層カスケードが動作しない | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#階層的カスケードが動作しない) |

> 📖 詳細な診断手順・デバッグ方法は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照

---

## 開発者向け

### Q: 新しい階層を追加できますか？

**A**: はい、`config.json`に新しいthresholdを追加し、`scripts/generate_digest_auto.sh`を更新することで追加可能です。

詳細は[ARCHITECTURE.md](../dev/ARCHITECTURE.md#拡張性)を参照してください。

### Q: カスタムエージェントを作成できますか？

**A**: はい、DigestAnalyzerエージェントをベースにカスタム分析ロジックを実装できます。

例：
- 特定ドメイン専用の分析エージェント
- 多言語対応分析エージェント
- 感情分析専門エージェント

### Q: テストの実行方法は？

**A**:
```bash
cd scripts
python -m pytest test/ -v
```

詳細は[ARCHITECTURE.md](../dev/ARCHITECTURE.md#テスト)を参照してください。

---

## 関連ドキュメント

- [GLOSSARY.md](../GLOSSARY.md) - 用語集
- [QUICKSTART.md](QUICKSTART.md) - 5分チュートリアル
- [GUIDE.md](GUIDE.md) - ユーザーガイド
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 詳細なトラブルシューティング
- [ARCHITECTURE.md](../dev/ARCHITECTURE.md) - 技術仕様

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
