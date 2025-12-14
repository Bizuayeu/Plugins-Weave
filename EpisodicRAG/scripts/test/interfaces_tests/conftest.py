#!/usr/bin/env python3
"""
Interfaces Tests Conftest
=========================

Interfaces層テスト用のpytestフィクスチャ定義。
テストは環境変数 EPISODICRAG_CONFIG_DIR を設定することで
get_persistent_config_dir() の戻り値を制御できる。
"""

# Note: このconftest.pyは空にして、各テストがsetUp()で
# 環境変数を設定するアプローチに移行。
# 事前にモジュールをインポートすると、テスト実行順序の問題が発生する。
