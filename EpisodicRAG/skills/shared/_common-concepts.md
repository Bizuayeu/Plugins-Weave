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

```
Loop (5個) → Weekly Digest
  ↓ (5個蓄積)
Weekly (5個) → Monthly Digest
  ↓ (3個蓄積)
Monthly (3個) → Quarterly Digest
  ↓ (4個蓄積)
Quarterly (4個) → Annual Digest
  ↓ (3個蓄積)
Annual (3個) → Triennial Digest
  ↓ (3個蓄積)
Triennial (3個) → Decadal Digest
  ↓ (3個蓄積)
Decadal (3個) → Multi-decadal Digest
  ↓ (4個蓄積)
Multi-decadal (4個) → Centurial Digest
```

---

*このファイルは内部参照用です。直接編集する場合は、参照元のドキュメントも確認してください。*
