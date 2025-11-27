# 共通概念（Common Concepts）

このファイルは、複数のドキュメントで共有される概念の定義を含みます。

---

## まだらボケとは

**まだらボケ** = AIがLoopの内容を記憶できていない（虫食い記憶）状態

### EpisodicRAGの本質

1. **Loopファイル追加** = 会話記録をファイルに保存（物理的保存）
2. **`/digest` 実行** = AIに記憶を定着させる（認知的保存）
3. **`/digest` なし** = ファイルはあるが、AIは覚えていない

### まだらボケが発生するケース

#### ケース1: 未処理Loopの放置（最も一般的）

```
Loop0001追加 → `/digest`せず → Loop0002追加
                              ↑
                    この時点でAIはLoop0001の内容を覚えていない
                    （記憶がまだら＝虫食い状態）
```

**対策**: Loopを追加したら都度`/digest`で記憶定着

#### ケース2: `/digest`処理中のエラー（技術的問題）

```
/digest 実行 → エラー発生 → ShadowGrandDigestに
                           source_filesは登録されたが
                           digestがnull（プレースホルダー）
```

**対策**: `/digest`を再実行して分析を完了

---

## 記憶定着サイクル

```
Loop追加 → `/digest` → Loop追加 → `/digest` → ...
         ↑ 記憶定着  ↑         ↑ 記憶定着
```

この原則を守ることで、AIは全てのLoopを記憶できます。

**やってはいけないこと:**

```
Loop0001追加 → `/digest`せず → Loop0002追加
                              ↑
                    この時点でAIはLoop0001の内容を覚えていない
                    （記憶がまだら＝虫食い状態）
```

---

## 階層的カスケード

> 📖 完全な8階層テーブル（プレフィックス・時間スケール含む）は [GLOSSARY.md](../../docs/GLOSSARY.md#8階層構造) を参照

```
Loop (5個) → Weekly Digest
  ↓
Weekly (5個) → Monthly Digest
  ↓
Monthly (3個) → Quarterly Digest
  ↓
Quarterly (4個) → Annual Digest
  ↓
Annual (3個) → Triennial Digest
  ↓
Triennial (3個) → Decadal Digest
  ↓
Decadal (3個) → Multi-decadal Digest
  ↓
Multi-decadal (4個) → Centurial Digest
```

---

## パス用語

| 用語 | 説明 |
|------|------|
| **plugin_root** | プラグインのインストール先（`.claude-plugin/config.json` が存在するディレクトリ） |
| **base_dir** | データ配置の基準ディレクトリ（plugin_root からの相対パスで指定） |
| **paths** | 各データディレクトリ（base_dir からの相対パスで指定） |

---

## 関連ドキュメント

- [GLOSSARY.md](../../docs/GLOSSARY.md) - 完全な用語定義（8階層構造、ファイル命名規則）
- [ARCHITECTURE.md](../../docs/dev/ARCHITECTURE.md) - 技術仕様・データフロー
- [GUIDE.md](../../docs/user/GUIDE.md) - ユーザーガイド

---

*このファイルは内部参照用です。直接編集する場合は、参照元のドキュメントも確認してください。*
