[EpisodicRAG](../../README.md) > [Docs](../README.md) > API_REFERENCE

# API リファレンス

EpisodicRAGプラグインの**Python API仕様書**です。

> **対応バージョン**: EpisodicRAG Plugin（[version.py](../../scripts/domain/version.py) 参照）/ ファイルフォーマット 1.0

> 📖 用語・共通概念: [用語集](../../README.md)

---

## このドキュメントの使い方

1. **新機能を実装したい** → Layer別APIから該当層を参照
2. **既存クラスの使い方を知りたい** → クイックリファレンスでインポートパスを確認
3. **設計判断の理由を知りたい** → [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)を参照
4. **全体像を把握したい** → [ARCHITECTURE.md](ARCHITECTURE.md)を参照

---

## このドキュメントの範囲

| 内容 | 配置先 |
|------|--------|
| **Python API**（クラス、関数、型定義） | **このドキュメント + api/*.md** |
| ファイル形式（GrandDigest/Shadow JSON構造） | [ARCHITECTURE.md](ARCHITECTURE.md#技術仕様) |
| データフロー図 | [ARCHITECTURE.md](ARCHITECTURE.md#データフロー) |
| 設定ファイル仕様（config.json） | [api/config.md](api/config.md) |

---

## Layer別API

Clean Architecture（4層構造）に基づいて、APIドキュメントを層別に分割しています。

| Layer | 説明 | ドキュメント |
|-------|------|-------------|
| **Domain** | コアビジネスロジック（定数、型、例外、ファイル命名） | [domain.md](api/domain.md) |
| **Infrastructure** | 外部関心事（JSON操作、ファイルスキャン、ロギング） | [infrastructure.md](api/infrastructure.md) |
| **Application** | ユースケース（Shadow管理、GrandDigest、Finalize処理） | [application.md](api/application.md) |
| **Interfaces** | エントリーポイント（DigestFinalizer、ProvisionalSaver） | [interfaces.md](api/interfaces.md) |
| **Config** | 設定管理（config.json仕様、DigestConfigクラス） | [config.md](api/config.md) |

---

## クイックリファレンス

### 推奨インポートパス

```python
# Domain層（定数・型・例外）
from domain import LEVEL_CONFIG, __version__, ValidationError
from domain.file_naming import extract_file_number, format_digest_number
from domain.level_registry import get_level_registry

# Infrastructure層（外部I/O）
from infrastructure import load_json, save_json, log_info, log_error
from infrastructure.file_scanner import scan_files
from infrastructure.user_interaction import get_default_confirm_callback

# Application層（ビジネスロジック）
from application.shadow import ShadowTemplate, ShadowUpdater, CascadeProcessor
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.finalize import RegularDigestBuilder, DigestPersistence
from application.validators import validate_dict, is_valid_list

# Interfaces層（エントリーポイント）
from interfaces import DigestFinalizerFromShadow, ProvisionalDigestSaver
from interfaces.interface_helpers import sanitize_filename, get_next_digest_number
from interfaces.provisional import InputLoader, DigestMerger

# 設定（configパッケージ）
from config import DigestConfig
```

### 依存関係ルール

```text
domain/           ← 何にも依存しない（純粋なビジネスロジック）
    ↑
infrastructure/   ← domain/ のみ
    ↑
application/      ← domain/ + infrastructure/
    ↑
interfaces/       ← application/
```

> 📖 **アーキテクチャ詳細**: [ARCHITECTURE.md](ARCHITECTURE.md#clean-architecture)

---

## デザインパターン

EpisodicRAGで使用されているデザインパターン一覧：

| パターン | 適用箇所 | 説明 |
|---------|---------|------|
| **Facade** | `DigestFinalizerFromShadow`, `ShadowGrandDigestManager`, `ShadowUpdater` | 複雑なサブシステムを単純なインターフェースで隠蔽 |
| **Repository** | `ShadowIO`, `GrandDigestManager`, `DigestTimesTracker` | データアクセスロジックの抽象化 |
| **Singleton** | `LevelRegistry` | 階層設定の一元管理（`get_level_registry()`で取得） |
| **Strategy** | `LevelBehavior`, `StandardLevelBehavior`, `LoopLevelBehavior` | 階層ごとの振る舞いを交換可能に |
| **Template Method** | `ShadowTemplate` | テンプレート生成の骨格定義 |
| **Builder** | `RegularDigestBuilder` | 複雑なオブジェクト（RegularDigest）の段階的構築 |
| **Factory** | `get_level_registry()`, `get_default_confirm_callback()` | オブジェクト生成の抽象化 |

> 📖 パターン選択の根拠: [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)

---

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - 技術仕様・データフロー
- [用語集](../../README.md) - 用語・共通概念
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発参加ガイド

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
