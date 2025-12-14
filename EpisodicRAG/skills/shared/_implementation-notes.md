# 実装ノート（Implementation Notes）

このファイルは、スキル・コマンド実装時の共通ガイドラインを含みます。

## 目次

**基盤**
- [DigestConfigへの依存](#digestconfigへの依存)
- [外部パスアクセス（trusted_external_paths）](#外部パスアクセスtrusted_external_paths)

**例外・検証**
- [エラーハンドリング](#エラーハンドリング)
- [バリデーションパターン](#バリデーションパターン)

**ドメイン固有ルール**
- [階層順序の維持](#階層順序の維持)
- [実装時の優先順位](#実装時の優先順位)

**出力・参考資料**
- [UIメッセージの出力形式](#uiメッセージの出力形式)
- [関連ドキュメント](#関連ドキュメント)

---

## DigestConfigへの依存

すべてのパス情報は`DigestConfig`（Facade）経由で取得します。

> 📖 **Config層は3層に分解されています（v4.0.0）**:
>
> | 層 | 責務 | 主要コンポーネント |
> |---|---|---|
> | `domain/config/` | 定数・型検証 | REQUIRED_CONFIG_KEYS, THRESHOLD_KEYS |
> | `infrastructure/config/` | ファイルI/O・パス解決 | ConfigLoader, PathResolver |
> | `application/config/` | バリデーション・サービス | DigestConfig (Facade), ConfigValidator |
>
> 📖 DigestConfig API: [api/config.md](../../docs/dev/api/config.md)
> 📖 実装詳細: [application/config/](../../scripts/application/config/__init__.py)

---

## 外部パスアクセス（trusted_external_paths）

v4.0.0で導入されたセキュリティ機能です。

**基本原則**:
- デフォルトでは`plugin_root`内のパスのみアクセス可能
- 外部パス（Loopsディレクトリ等）を使用する場合、明示的なホワイトリスト登録が必要

```json
// config.json
{
  "trusted_external_paths": ["~/DEV/production/Loops"]
}
```

**注意事項**:
- 許可されていないパスへのアクセスは `PathSecurityError` 例外が発生
- チルダ展開（`~`）は対応、相対パスは禁止
- 空配列 `[]` の場合、plugin_root内のみアクセス可能

> 📖 詳細仕様: [api/config.md](../../docs/dev/api/config.md)

---

## エラーハンドリング

### 例外クラス

> 📖 カスタム例外クラスは [domain/exceptions.py](../../scripts/domain/exceptions.py) を参照

### エラー処理パターン

> 📖 共通エラーハンドリングは [infrastructure/error_handling.py](../../scripts/infrastructure/error_handling.py) を参照

### 基本方針

- config.jsonは `@digest-setup` で作成される
- GrandDigest.txt / ShadowGrandDigest.txt は `load_or_create()` パターンで自動作成

---

## バリデーションパターン

> 📖 バリデーション関数は [domain/validators/](../../scripts/domain/validators/) を参照

### バリデーション種別

| 種別 | 参照先 |
|------|--------|
| 型検証 | `domain/validators/type_validators.py` |
| Digest検証 | `domain/validators/digest_validators.py` |
| ランタイムチェック | `domain/validators/runtime_checks.py` |

---

## 階層順序の維持

階層的カスケードのため、必ず下位階層から順に生成する必要があります：

```text
Weekly → Monthly → Quarterly → Annual →
Triennial → Decadal → Multi-decadal → Centurial
```

推奨アクションでは、常に最下位の生成可能な階層を優先して提示します。

---

## 実装時の優先順位

まだらボケ予防のため、以下の順序でチェックを実行します：

1. **未処理Loop検出** → 警告して即終了
2. **プレースホルダー検出** → 警告して即終了
3. **中間ファイルスキップ検出** → 警告のみ（処理継続）
4. **通常の判定フロー** → 生成可能な階層を表示

---

## UIメッセージの出力形式

**重要**: VSCode拡張のマークダウンレンダリングでは、単一の改行は空白に変換されます。
対話型UIメッセージを表示する際は、必ず**コードブロック（三連バッククォート）**で囲んでください。

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 タイトル
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

メッセージ内容

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

これにより、改行がそのまま保持され、ユーザーに正しくフォーマットされたメッセージが表示されます。

---

## 関連ドキュメント

- [用語集・リファレンス](../../README.md) - 用語定義・共通概念
- [API_REFERENCE.md](../../docs/dev/API_REFERENCE.md) - DigestConfig API
- [ARCHITECTURE.md](../../docs/dev/ARCHITECTURE.md) - 技術仕様
- [interfaces/](../../scripts/interfaces/) - Python化スキル実装（digest_setup, digest_config, digest_auto）

---

*このファイルはClaude向けの内部参照用です。*
