[EpisodicRAG](../../README.md) > [Docs](../README.md) > FAQ

# よくある質問 (FAQ)

EpisodicRAGプラグインに関するよくある質問と回答集です。

---

## このドキュメントの使い方

| 質問の種類 | 参照先 |
|-----------|--------|
| 「〜とは何か」「なぜ〜か」という**概念的な疑問** | **このドキュメント（FAQ）** |
| 「〜が動かない」「〜を修復したい」という**具体的な問題解決** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

> 💡 FAQ で概念を理解し、問題が発生したら TROUBLESHOOTING で解決手順を確認してください。

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

**A**: AI会話履歴を8階層で構造化し、セッション間で記憶を引き継ぐプラグインです。

> 📖 詳細: [用語集](../../README.md)

### Q: 無料で使えますか？

**A**: 個人・非商用利用はMITライセンスで自由に利用可能。商用利用は特許権の関係で事前相談が必要です。

### Q: どのAI環境で動作しますか？

**A**: Claude Code（CLI）、Claude VSCode Extension、Claude WebChat（一部制限）で動作します。

---

## 導入・セットアップ

### Q: インストールに失敗します

**A**: マーケットプレイス追加（`/marketplace list`で確認）→ プラグイン名確認（`EpisodicRAG-Plugin@Plugins-Weave`）→ ネットワーク確認の順でチェック。

> 📖 詳細: [QUICKSTART.md](QUICKSTART.md)

### Q: 設定ファイルが見つかりません

**A**: `@digest-setup` を実行。設定ファイルは自動作成されます。

### Q: パスが正しく解決されません

**A**: `@digest-config` で設定を確認・修正。`base_dir`がプラグインルート基準であることを確認。

> 📖 詳細: [用語集](../../README.md#基本概念)、[api/config.md](../dev/api/config.md#configjson-詳細仕様)

---

## 日常的な使い方

### Q: Loopファイルの命名規則は？

**A**: `L[連番]_[タイトル].txt` の形式です（連番は5桁ゼロ埋め）。

**例**: `L00001_認知アーキテクチャ論.txt`

> 📖 詳細（正規表現・連番ルール）は [用語集 > ファイル命名規則](../../README.md#ファイル命名規則) を参照

### Q: `/digest`と`/digest weekly`の違いは？

**A**:
- **`/digest`**: Loopを追加したら都度実行（記憶定着）
- **`/digest weekly`**: 5個溜まったら実行（確定）

```mermaid
flowchart TB
    subgraph everyday["📅 毎日（Loop追加ごと）"]
        D1["/digest"]
        D1 --> |記憶定着| S1[ShadowGrandDigest更新]
    end

    subgraph weekly["📆 週次（5個揃ったら）"]
        D2["/digest weekly"]
        D2 --> |確定| R1[Regular Digest作成]
    end

    S1 -.->|蓄積| D2

    style D1 fill:#90EE90
    style D2 fill:#FFD700
```

> 📖 実行フロー・データフローの詳細は [GUIDE.md > コマンド詳解](GUIDE.md#digest-コマンド) を参照

### Q: まだらボケとは何ですか？

**A**: AIがLoopの内容を記憶できていない状態です。`Loop追加 → /digest`のサイクルで予防できます。

> 📖 発生パターン・対策・記憶定着サイクルの詳細は [用語集](../../README.md#まだらボケ) を参照

### Q: threshold（閾値）を変更したい

**A**: `@digest-config` → [4] Thresholds を選択。

> 📖 詳細: [API_REFERENCE.md](../dev/API_REFERENCE.md#config.json-詳細仕様)

---

## トラブルシューティング

問題が発生した場合は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照してください。

症状別の解決手順、診断フローチャート、デバッグ方法が記載されています。

---

## 開発者向け

### Q: 新しい階層を追加できますか？

**A**: はい。`config.json`にthreshold追加 + `domain/constants.py`のLEVEL_CONFIG更新で可能。

> 📖 詳細: [ARCHITECTURE.md](../dev/ARCHITECTURE.md#拡張性)

### Q: カスタムエージェントを作成できますか？

**A**: はい。DigestAnalyzerをベースにカスタム分析ロジックを実装可能（ドメイン専用、多言語対応、感情分析など）。

### Q: テストの実行方法は？

**A**: `cd scripts && python -m pytest test/ -v`

> 📖 詳細: [ARCHITECTURE.md](../dev/ARCHITECTURE.md#テスト)、[CONTRIBUTING.md](../../CONTRIBUTING.md#テスト)

### Q: ドキュメント内で特定のキーワードを検索したい

**A**: GitHubの検索機能またはローカル検索を使用してください。

```text
# リポジトリ内検索（GitHub Web）
https://github.com/Bizuayeu/Plugins-Weave で "キーワード" を検索

# ローカル検索（VS Code）
Ctrl+Shift+F → plugins-weave フォルダで検索
```

> 💡 主要な用語は [用語集](../../README.md#用語インデックス) にインデックスがあります。

---

## 関連ドキュメント

- [用語集](../../README.md) - 用語・共通概念
- [QUICKSTART.md](QUICKSTART.md) - 5分チュートリアル
- [GUIDE.md](GUIDE.md) - ユーザーガイド
- [CHEATSHEET.md](CHEATSHEET.md) - コマンド早見表
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 詳細なトラブルシューティング
- [ARCHITECTURE.md](../dev/ARCHITECTURE.md) - 技術仕様

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
