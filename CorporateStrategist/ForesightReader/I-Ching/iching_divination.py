#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周易占断システム - I-Ching Divination Engine
占的と占機から64卦384爻を導き出す計算エンジン
"""

import json
import base64
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class IChingDivination:
    """周易占断クラス"""

    def __init__(self, database_path: Optional[str] = None):
        """
        初期化

        Args:
            database_path: 大卦データベースのパス
        """
        if database_path is None:
            # デフォルトパス
            current_dir = Path(__file__).parent
            database_path = current_dir / "大卦データベース.json"

        with open(database_path, 'r', encoding='utf-8') as f:
            self.database = json.load(f)

        self.hexagrams = self.database['hexagrams']

    def get_hexagram_number(self, divination_question: str, context: str) -> int:
        """
        占的文字列と状況整理から卦番号（1-64）を決定
        天地人の三才思想に基づき、ハッシュを3分割してXOR演算

        Args:
            divination_question: 占的（明確化された問い）
            context: 状況整理文書（背景情報）※必須

        Returns:
            卦番号（1-64）
        """
        # 至誠通天 - 誠の心が天に通じる
        print("至誠通天 - 誠の心をもって問いを天に届けます")

        # 占的と状況整理を結合（状況が個別性を生む）
        complete_question = f"{divination_question}\n===状況整理===\n{context}"

        # UTF-8エンコード → BASE64
        encoded = base64.b64encode(complete_question.encode('utf-8'))

        # SHA256でハッシュ化（安定した分散を得るため）
        hash_value = hashlib.sha256(encoded).hexdigest()

        # 天地人の三才に分割（SHA256は64文字）
        # 天：最初の16文字（64ビット - 上界の意志）
        天 = int(hash_value[:16], 16)

        # 地：中間の32文字（128ビット - 天と人を支える基盤）
        地 = int(hash_value[16:48], 16)

        # 人：最後の16文字（64ビット - 人間の問い）
        人 = int(hash_value[48:64], 16)

        # 三才をXOR演算で統合（天地人の調和）
        三才統合 = 天 ^ 地 ^ 人

        # 64卦への変換
        number = 三才統合 % 64 + 1

        return number

    def get_line_number(self, timestamp: Optional[float] = None) -> int:
        """
        タイムスタンプから爻番号（1-6）を決定

        Args:
            timestamp: Unixタイムスタンプ（省略時は現在時刻）

        Returns:
            爻番号（1-6）
        """
        if timestamp is None:
            timestamp = time.time()

        # ミリ秒単位に変換
        timestamp_ms = int(timestamp * 1000)

        # mod6で0-5、+1で1-6に変換
        line_number = timestamp_ms % 6 + 1

        return line_number

    def get_hexagram_data(self, hexagram_number: int) -> Dict[str, Any]:
        """
        卦番号から卦データを取得

        Args:
            hexagram_number: 卦番号（1-64）

        Returns:
            卦データ
        """
        # 番号は1始まり、配列は0始まり
        hexagram = self.hexagrams[hexagram_number - 1]
        return hexagram

    def get_line_data(self, hexagram_number: int, line_number: int) -> Dict[str, Any]:
        """
        卦番号と爻番号から爻データを取得

        Args:
            hexagram_number: 卦番号（1-64）
            line_number: 爻番号（1-6）

        Returns:
            爻データ
        """
        hexagram = self.get_hexagram_data(hexagram_number)
        # 爻番号も1始まり、配列は0始まり
        line = hexagram['爻'][line_number - 1]
        return line

    def divine(self, divination_question: str, context: str, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        占断を実行

        Args:
            divination_question: 占的（明確化された問い）
            context: 状況整理文書（背景情報）※必須
            timestamp: Unixタイムスタンプ（省略時は現在時刻）

        Returns:
            占断結果の辞書。以下の構造を持つ：
            {
                '占機': {
                    '日時': str,  # 'YYYY年MM月DD日 HH時MM分SS秒'
                    'タイムスタンプ': float
                },
                '占的': str,  # 入力された占的
                '状況整理': str,  # 入力された状況整理または「（状況整理なし）」
                '得卦': {
                    '番号': int,  # 1-64
                    '名前': str,  # 例：'沢風大過'
                    '読み': str,  # 例：'たくふうたいか'
                    'シンボル': str,  # 易経のシンボル文字
                    'バイナリ': str,  # '011110' など6桁の2進数文字列
                    '卦辞': str,  # 原文の卦辞
                    '上卦': dict,  # {'名前': str, '象意': str, '性質': str}
                    '下卦': dict   # {'名前': str, '象意': str, '性質': str}
                },
                '得爻': {
                    '番号': int,  # 1-6
                    '名前': str,  # 例：'六五'
                    '陰陽': str,  # '陰' または '陽'
                    '爻辞': str   # 原文の爻辞
                }
            }
        """
        # 至誠無息 - 誠の心は休むことなく続く
        print("\n至誠無息 - 誠実な問いには誠実な答えが返ります\n")

        # 占機（時刻）の記録
        if timestamp is None:
            timestamp = time.time()
        divination_time = datetime.fromtimestamp(timestamp)

        # 卦番号と爻番号の算出
        hexagram_number = self.get_hexagram_number(divination_question, context)
        line_number = self.get_line_number(timestamp)

        # データ取得
        hexagram_data = self.get_hexagram_data(hexagram_number)
        line_data = self.get_line_data(hexagram_number, line_number)

        # 八卦の分析（バイナリ表現から上卦・下卦を導出）
        binary = hexagram_data['バイナリ']
        upper_trigram = binary[:3]  # 上卦（上位3ビット）
        lower_trigram = binary[3:]  # 下卦（下位3ビット）

        # 八卦の対応表
        trigrams = {
            '111': {'名前': '乾', '象意': '天', '性質': '剛健'},
            '110': {'名前': '兌', '象意': '沢', '性質': '悦楽'},
            '101': {'名前': '離', '象意': '火', '性質': '明智'},
            '100': {'名前': '震', '象意': '雷', '性質': '震動'},
            '011': {'名前': '巽', '象意': '風', '性質': '柔順'},
            '010': {'名前': '坎', '象意': '水', '性質': '険難'},
            '001': {'名前': '艮', '象意': '山', '性質': '静止'},
            '000': {'名前': '坤', '象意': '地', '性質': '柔順'}
        }

        upper_trigram_data = trigrams.get(upper_trigram, {})
        lower_trigram_data = trigrams.get(lower_trigram, {})

        # 結果を構造化
        result = {
            '占機': {
                '日時': divination_time.strftime('%Y年%m月%d日 %H時%M分%S秒'),
                'タイムスタンプ': timestamp
            },
            '占的': divination_question,
            '状況整理': context,
            '得卦': {
                '番号': hexagram_number,
                '名前': hexagram_data['名前'],
                '読み': hexagram_data['読み'],
                'シンボル': hexagram_data['シンボル'],
                'バイナリ': hexagram_data['バイナリ'],
                '卦辞': hexagram_data['卦辞'],
                '上卦': upper_trigram_data,
                '下卦': lower_trigram_data
            },
            '得爻': {
                '番号': line_number,
                '名前': line_data['名前'],
                '陰陽': line_data['陰陽'],
                '爻辞': line_data['爻辞']
            }
        }

        return result

    def format_result(self, result: Dict[str, Any]) -> str:
        """
        占断結果を読みやすい形式に整形

        Args:
            result: divine()の結果

        Returns:
            整形された文字列
        """
        lines = []
        lines.append("=" * 60)
        lines.append("周易占断結果")
        lines.append("=" * 60)
        lines.append(f"占機：{result['占機']['日時']}")
        lines.append(f"占的：{result['占的']}")
        lines.append("")

        得卦 = result['得卦']
        lines.append(f"【得卦】{得卦['番号']}. {得卦['名前']}（{得卦['読み']}）")
        lines.append(f"シンボル：{得卦['シンボル']}")
        lines.append(f"バイナリ：{得卦['バイナリ']}")

        if 得卦['上卦']:
            lines.append(f"上卦：{得卦['上卦']['名前']}（{得卦['上卦']['象意']}）- {得卦['上卦']['性質']}")
        if 得卦['下卦']:
            lines.append(f"下卦：{得卦['下卦']['名前']}（{得卦['下卦']['象意']}）- {得卦['下卦']['性質']}")

        lines.append("")
        lines.append(f"卦辞：{得卦['卦辞']}")
        lines.append("")

        得爻 = result['得爻']
        lines.append(f"【得爻】第{得爻['番号']}爻 - {得爻['名前']}（{得爻['陰陽']}）")
        lines.append(f"爻辞：{得爻['爻辞']}")
        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """直接実行時の警告とガイダンス"""
    print("=" * 80)
    print("WARNING: Direct Execution Mode / 警告：直接実行モード")
    print("=" * 80)
    print()
    print("このスクリプトを正しく使用するには、先に以下のドキュメントを必ずお読みください：")
    print()
    print("1. デジタル心易システム仕様.md")
    print("   場所: ./（相対パス）")
    print("   内容: デジタル心易の理論、思想、実装詳細")
    print()
    print("2. ../CLAUDE.md")
    print("   場所: ../（相対パス）")
    print("   内容: 軍師型占術家システム全体の仕様")
    print()
    print("-" * 40)
    print("[推奨される使用方法]")
    print()
    print("このスクリプトは直接実行せず、")
    print("Claudeの対話内でライブラリとしてインポートして使用します：")
    print()
    print(">>> import sys")
    print(">>> from pathlib import Path")
    print(">>> # Weaveプロジェクトルートを探す（環境非依存）")
    print(">>> cwd = Path.cwd()")
    print(">>> weave_root = cwd if cwd.name == 'Weave' else next((p for p in cwd.parents if p.name == 'Weave'), cwd)")
    print(">>> iching_path = weave_root / 'Expertises/CorporateStrategist/ForesightReader/I-Ching'")
    print(">>> sys.path.append(str(iching_path))")
    print(">>> from iching_divination import IChingDivination")
    print(">>> ")
    print(">>> divination = IChingDivination()")
    print(">>> result = divination.divine(")
    print(">>>     divination_question='占的文字列',")
    print(">>>     context='状況整理文書'")
    print(">>> )")
    print()
    print("-" * 40)
    print("[重要な注意事項]")
    print()
    print("・占的の明確化が最も重要です")
    print("・状況整理を加えることで個別性が高まります")
    print("・結果はDivineTemplate.mdで整形して出力します")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()