import json
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

"""
七格剖象法による姓名判定システム

このモジュールは、姓名の画数から7つの格
（天格・地格・人格・総格・外格・雲格・底格）を計算し、
各格に対応する数霊・星導・吉凶などの情報を
JSONデータと結合して鑑定結果を生成します。
"""

@dataclass
class Character:
    """文字とその画数を保持するデータクラス"""
    char: str        # 文字
    strokes: int     # 画数

    def __repr__(self):
        return f"{self.char}({self.strokes}画)"

@dataclass
class NameComponents:
    """姓と名の文字情報と格納順を管理するデータクラス"""
    surname: List[Character] = field(default_factory=list)     # 姓の文字リスト（順序保持）
    given_name: List[Character] = field(default_factory=list)  # 名の文字リスト（順序保持）

@dataclass
class Frame:
    """各格（天格、地格など）の情報を保持するデータクラス"""
    name: str                           # 格の名前（天格、地格など）
    value: int                          # 格の数値
    spirit_number: Optional[int] = None  # 数霊番号（1-91）
    system_number: Optional[int] = None  # 系数（一の位）
    secret_number: Optional[int] = None  # 秘数（数字根）
    system_star: Optional[str] = None   # 系数の星導（天体）
    secret_star: Optional[str] = None   # 秘数の星導（天体）
    fortune: Optional[str] = None       # 吉凶
    meaning: Optional[str] = None       # 象意
    ten_stems: Optional[str] = None     # 十干（甲乙丙丁戊己庚辛壬癸）
    five_elements: Optional[str] = None # 五行（木火土金水）

@dataclass
class SevenFrames:
    """七格すべてを管理するデータクラス"""
    天格: Frame  # 家系・先祖の運勢
    地格: Frame  # 幼少期・本質
    人格: Frame  # 才能・人格・意志の方向
    総格: Frame  # 人生全体の特徴
    外格: Frame  # 他者からの評価・第一印象
    雲格: Frame  # 仕事の満足度・職場の人間関係
    底格: Frame  # 家族の満足度・夫婦関係

    def all_frames(self) -> List[Frame]:
        """すべての格をリストで返す"""
        return [self.天格, self.地格, self.人格, self.総格, self.外格, self.雲格, self.底格]

@dataclass
class StarDistribution:
    """星導（天体）の分布をカウントするデータクラス"""
    太陽: int = 0     # 創造
    月: int = 0       # 静寂
    木星: int = 0     # 発展
    天王星: int = 0   # 変化
    水星: int = 0     # 調和
    金星: int = 0     # 豊饒
    海王星: int = 0   # 信念
    土星: int = 0     # 忍耐
    火星: int = 0     # 闘争
    冥王星: int = 0   # 終末

    def to_dict(self) -> Dict[str, int]:
        """辞書形式で出力"""
        return {
            "太陽": self.太陽,
            "月": self.月,
            "木星": self.木星,
            "天王星": self.天王星,
            "水星": self.水星,
            "金星": self.金星,
            "海王星": self.海王星,
            "土星": self.土星,
            "火星": self.火星,
            "冥王星": self.冥王星
        }

@dataclass
class PersonnelTypes:
    """人材4類型の度数を管理するデータクラス"""
    軍人度: int = 0  # 火星+冥王星：危機的状況での決断者
    天才度: int = 0  # 天王星+海王星：創造的革新者
    秀才度: int = 0  # 太陽+木星+水星：平和的調整者
    凡人度: int = 0  # 月+金星+土星：堅実な実行者

    def to_dict(self) -> Dict[str, int]:
        """辞書形式で出力"""
        return {
            "軍人度": self.軍人度,
            "天才度": self.天才度,
            "秀才度": self.秀才度,
            "凡人度": self.凡人度
        }

class FortuneTellerAssessment:
    """七格剖象法による姓名判定を実行するメインクラス"""

    def __init__(self, json_dir: str = None):
        """JSONデータファイルを読み込んで初期化

        Args:
            json_dir: JSONファイルが格納されているディレクトリパス
                     Noneの場合は実行ファイルと同じディレクトリを使用
        """
        # JSONファイルのディレクトリを決定
        if json_dir is None:
            json_dir = Path(__file__).parent
        else:
            json_dir = Path(json_dir)

        # 各種JSONデータを読み込み
        self.spirit_table = self._load_json(json_dir / "ここのそ数霊表.json")      # 数霊表（1-91の吉凶・象意）
        self.star_guide = self._load_json(json_dir / "数理星導一覧.json")         # 数字と天体の対応表
        self.five_elements = self._load_json(json_dir / "五気判定マトリックス.json")  # 五行相生相剋表
        self.yin_yang = self._load_json(json_dir / "陰陽配列パターン.json")       # 陰陽配列の判定表

    def _load_json(self, filepath: Path) -> dict:
        """JSONファイルを読み込む

        Args:
            filepath: JSONファイルのパス
        Returns:
            読み込んだJSONデータ
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_name(self, surname: str, given_name: str, surname_strokes: List[int], given_strokes: List[int]) -> NameComponents:
        """姓名を文字単位に分解して画数と共に格納

        Args:
            surname: 姓（例："大神"）
            given_name: 名（例："加五郎兵衛"）
            surname_strokes: 姓の各文字の画数リスト（必須。例：[3, 9]）
            given_strokes: 名の各文字の画数リスト（必須。例：[5, 4, 9, 7, 16]）

        Returns:
            NameComponents: 文字ごとの画数を順序保持で格納したオブジェクト
        """
        components = NameComponents()

        # ===== 姓の処理 =====
        # 例："大神" → [Character("大", 3), Character("神", 9)]
        for i, char in enumerate(surname):
            if i < len(surname_strokes):
                # 画数リストから取得
                strokes = surname_strokes[i]
            elif char == '々' and i > 0:
                # 「々」は前の文字の画数を引き継ぐ
                strokes = components.surname[i-1].strokes if components.surname else 3
            else:
                # 画数が不明な場合はエラー
                raise ValueError(f"姓の文字「{char}」（{i+1}文字目）の画数が指定されていません。surname_strokes引数で画数を提供してください。")
            components.surname.append(Character(char, strokes))

        # ===== 名の処理 =====
        # 例："加五郎兵衛" → [Character("加", 5), Character("五", 4), ...]
        for i, char in enumerate(given_name):
            if i < len(given_strokes):
                # 画数リストから取得
                strokes = given_strokes[i]
            elif char == '々' and i > 0:
                # 「々」は前の文字の画数を引き継ぐ
                strokes = components.given_name[i-1].strokes if components.given_name else 3
            else:
                # 画数が不明な場合はエラー
                raise ValueError(f"名の文字「{char}」（{i+1}文字目）の画数が指定されていません。given_strokes引数で画数を提供してください。")
            components.given_name.append(Character(char, strokes))

        return components

    def calculate_main_frames(self, components: NameComponents) -> Tuple[int, int, int, int, int]:
        """主要五格（天格・地格・人格・総格・外格）を計算

        主要五格では霊数を使用しない（霊数は雲格・底格のみで使用）

        Args:
            components: 姓名の文字情報

        Returns:
            天格, 地格, 人格, 総格, 外格の値のタプル
        """
        # 画数リストを作成
        surname_strokes = [c.strokes for c in components.surname]  # 例：[3, 9]
        given_strokes = [c.strokes for c in components.given_name]  # 例：[5, 4, 9, 7, 16]

        # ===== 天格の計算 =====
        # 姓の画数の合計（霊数なし）
        天格 = sum(surname_strokes)

        # ===== 地格の計算 =====
        # 名の画数の合計（霊数なし）
        地格 = sum(given_strokes)

        # ===== 人格の計算 =====
        # 姓の最後の文字と名の最初の文字の画数合計
        surname_last = surname_strokes[-1] if surname_strokes else 0
        given_first = given_strokes[0] if given_strokes else 0
        人格 = surname_last + given_first

        # ===== 総格の計算 =====
        # 姓名すべての画数の合計
        総格 = sum(surname_strokes) + sum(given_strokes)

        # ===== 外格の計算 =====
        # 総格から人格を引く。1字姓1字名の場合は特殊ルール
        if len(surname_strokes) == 1 and len(given_strokes) == 1:
            # 1字姓1字名の特殊ルール：人格=総格=外格
            外格 = 総格
        else:
            # 通常：総格 - 人格
            外格 = 総格 - 人格

        return 天格, 地格, 人格, 総格, 外格

    def calculate_supplementary_frames(self, components: NameComponents, 総格: int) -> Tuple[int, int]:
        """補助格（雲格・底格）を計算

        1字姓や1字名の場合に霊数1を加える複雑な計算を行う

        Args:
            components: 姓名の文字情報
            総格: 総格の値

        Returns:
            雲格, 底格の値のタプル
        """
        surname_strokes = [c.strokes for c in components.surname]
        given_strokes = [c.strokes for c in components.given_name]

        # 1字姓/1字名の判定
        is_single_surname = len(surname_strokes) == 1
        is_single_given = len(given_strokes) == 1

        # ===== 雲格の計算 =====
        # 仕事の満足度・職場の人間関係を表す
        if is_single_surname and is_single_given:
            # 1字姓 & 1字名：総格 + 霊数1
            雲格 = 総格 + 1
        elif is_single_surname and not is_single_given:
            # 1字姓 & 2字以上の名：総格 + 霊数1 - 名の最後の文字の画数
            雲格 = 総格 + 1 - given_strokes[-1]
        elif not is_single_surname and is_single_given:
            # 2字以上の姓 & 1字名：総格のまま
            雲格 = 総格
        else:
            # 2字以上の姓 & 2字以上の名：総格 - 名の最後の文字の画数
            雲格 = 総格 - given_strokes[-1]

        # ===== 底格の計算 =====
        # 家族の満足度・夫婦関係を表す
        if is_single_surname and is_single_given:
            # 1字姓 & 1字名：総格 + 霊数1
            底格 = 総格 + 1
        elif is_single_surname and not is_single_given:
            # 1字姓 & 2字以上の名：総格のまま
            底格 = 総格
        elif not is_single_surname and is_single_given:
            # 2字以上の姓 & 1字名：総格 + 霊数1 - 姓の最初の文字の画数
            底格 = 総格 + 1 - surname_strokes[0]
        else:
            # 2字以上の姓 & 2字以上の名：総格 - 姓の最初の文字の画数
            底格 = 総格 - surname_strokes[0]

        return 雲格, 底格

    def get_spirit_info(self, number: int) -> Dict:
        """数霊表から該当する数霊情報を取得

        91を超える場合は90で循環させる（91→1、92→2...）

        Args:
            number: 格の数値

        Returns:
            数霊情報（吉凶、象意、系数、秘数など）
        """
        # まず直接検索
        for spirit in self.spirit_table:
            if spirit["数霊"] == number:
                return spirit

        # 91以上の場合は90で循環
        # 例：92 → ((92-1) % 90) + 1 = 2
        adjusted = ((number - 1) % 90) + 1
        for spirit in self.spirit_table:
            if spirit["数霊"] == adjusted:
                return spirit
        return None

    def get_star_from_number(self, number: int) -> str:
        """数字（0-9）から対応する星導（天体）を取得

        系数（一の位）や秘数（数字根）として渡される0-9の数字から
        対応する天体を取得する

        Args:
            number: 0-9の数字（系数または秘数）

        Returns:
            星導と象徴（例："太陽(創造)"）
        """
        # 一の位を取得（念のため。通常は0-9が渡される）
        digit = number % 10

        # 数理星導一覧から対応する星導を検索
        for star_info in self.star_guide:
            if star_info["数霊"] == digit:
                return f"{star_info['星導']}({star_info['象徴']})"
        return None

    def create_frame(self, name: str, value: int) -> Frame:
        """格の数値から詳細情報を付加したFrameオブジェクトを作成

        Args:
            name: 格の名前（天格、地格など）
            value: 格の数値

        Returns:
            Frame: 数霊情報と星導情報を持つFrameオブジェクト
        """
        # 数霊表から情報を取得
        spirit_info = self.get_spirit_info(value)

        # 系数と秘数の取得
        system_number = spirit_info["系数"] if spirit_info else None
        secret_number = spirit_info["秘数"] if spirit_info else None

        # 系数と秘数の星導を個別に取得
        system_star = self.get_star_from_number(system_number) if system_number is not None else None
        secret_star = self.get_star_from_number(secret_number) if secret_number is not None else None

        # 系数から十干と五行を決定
        ten_stems = None
        five_elements = None

        if system_number is not None:
            ten_stems_map = {0: "癸", 1: "甲", 2: "乙", 3: "丙", 4: "丁", 5: "戊", 6: "己", 7: "庚", 8: "辛", 9: "壬"}
            five_elements_map = {0: "水", 1: "木", 2: "木", 3: "火", 4: "火", 5: "土", 6: "土", 7: "金", 8: "金", 9: "水"}
            ten_stems = ten_stems_map.get(system_number, "不明")
            five_elements = five_elements_map.get(system_number, "不明")

        # Frameオブジェクトを作成
        frame = Frame(
            name=name,
            value=value,
            spirit_number=value if value <= 91 else ((value - 1) % 90) + 1,  # 91超は循環
            system_number=system_number,                                     # 一の位
            secret_number=secret_number,                                     # 数字根
            system_star=system_star,                                        # 系数の星導
            secret_star=secret_star,                                        # 秘数の星導
            fortune=spirit_info["吉凶"] if spirit_info else None,           # 吉凶判定
            meaning=spirit_info["象意"] if spirit_info else None,           # 象意
            ten_stems=ten_stems,                                            # 十干
            five_elements=five_elements                                     # 五行
        )
        return frame

    def calculate_seven_frames(self, components: NameComponents) -> SevenFrames:
        """七格すべてを計算してJSONデータと結合

        Args:
            components: 姓名の文字情報

        Returns:
            SevenFrames: 七格すべての情報を持つオブジェクト
        """
        # Step 1: 主要五格を計算
        天格, 地格, 人格, 総格, 外格 = self.calculate_main_frames(components)

        # Step 2: 補助格を計算
        雲格, 底格 = self.calculate_supplementary_frames(components, 総格)

        # Step 3: 各格にJSONデータを結合してFrameオブジェクトを作成
        frames = SevenFrames(
            天格=self.create_frame("天格", 天格),
            地格=self.create_frame("地格", 地格),
            人格=self.create_frame("人格", 人格),
            総格=self.create_frame("総格", 総格),
            外格=self.create_frame("外格", 外格),
            雲格=self.create_frame("雲格", 雲格),
            底格=self.create_frame("底格", 底格)
        )

        return frames

    def calculate_star_distribution(self, frames: SevenFrames) -> StarDistribution:
        """七格の星導（天体）の分布をカウント

        各格の系数と秘数がどの天体に対応するかを集計して、
        天体ごとの出現回数をカウントする（各格につき2つの天体）

        Args:
            frames: 七格の情報

        Returns:
            StarDistribution: 10天体ごとのカウント結果（合計14）
        """
        distribution = StarDistribution()

        # 各格の星導をカウント
        for frame in frames.all_frames():
            # ===== 系数（一の位）の星導をカウント =====
            if frame.system_star:
                # Frameに保存された系数星導を使用
                star_name = frame.system_star.split("(")[0]
                if hasattr(distribution, star_name):
                    setattr(distribution, star_name,
                           getattr(distribution, star_name) + 1)

            # ===== 秘数（数字根）の星導をカウント =====
            if frame.secret_star:
                # Frameに保存された秘数星導を使用
                star_name = frame.secret_star.split("(")[0]
                if hasattr(distribution, star_name):
                    setattr(distribution, star_name,
                           getattr(distribution, star_name) + 1)

        return distribution

    def calculate_personnel_types(self, frames: SevenFrames) -> PersonnelTypes:
        """人材4類型の度数を計算

        各天体を4つのタイプに分類し、七格の系数・秘数の星導から
        各タイプの度数を集計する。人格と総格は2倍カウント。

        Args:
            frames: 七格の情報

        Returns:
            PersonnelTypes: 4類型ごとの度数（合計18）
        """
        types = PersonnelTypes()

        # 天体と人材タイプの対応表
        personnel_map = {
            "火星": "軍人度",      # 闘争
            "冥王星": "軍人度",    # 終末
            "天王星": "天才度",    # 変化
            "海王星": "天才度",    # 信念
            "太陽": "秀才度",      # 創造
            "木星": "秀才度",      # 発展
            "水星": "秀才度",      # 調和
            "月": "凡人度",        # 静寂
            "金星": "凡人度",      # 豊饒
            "土星": "凡人度"       # 忍耐
        }

        # 各格の星導から人材タイプを集計
        for frame in frames.all_frames():
            # ★重要：人格と総格は2倍カウント
            multiplier = 2 if frame.name in ["人格", "総格"] else 1

            # ===== 系数（一の位）の星導から集計 =====
            if frame.system_star:
                star_name = frame.system_star.split("(")[0]
                if star_name in personnel_map:
                    personnel_type = personnel_map[star_name]
                    current_value = getattr(types, personnel_type)
                    setattr(types, personnel_type, current_value + multiplier)

            # ===== 秘数（数字根）の星導から集計 =====
            if frame.secret_star:
                star_name = frame.secret_star.split("(")[0]
                if star_name in personnel_map:
                    personnel_type = personnel_map[star_name]
                    current_value = getattr(types, personnel_type)
                    setattr(types, personnel_type, current_value + multiplier)

        return types

    def assess(self, surname: str, given_name: str, surname_strokes: List[int], given_strokes: List[int]) -> Dict:
        """姓名判定のメインメソッド

        姓名と画数を受け取り、七格剖象法による鑑定結果を返す

        Args:
            surname: 姓（例："大神"）
            given_name: 名（例："加五郎兵衛"）
            surname_strokes: 姓の各文字の画数リスト（必須。例：[3, 9]）
            given_strokes: 名の各文字の画数リスト（必須。例：[5, 4, 9, 7, 16]）

        Returns:
            鑑定結果の辞書（七格、星導分布、人材4類型など）
        """
        # ===== Step 1: 姓名を文字単位に分解 =====
        components = self.parse_name(surname, given_name, surname_strokes, given_strokes)

        # ===== Step 2: 七格を計算してJSONデータと結合 =====
        frames = self.calculate_seven_frames(components)

        # ===== Step 3: 星導分布図を作成（10天体ごとのカウント） =====
        star_distribution = self.calculate_star_distribution(frames)

        # ===== Step 4: 人材4類型を計算（人格・総格は2倍） =====
        personnel_types = self.calculate_personnel_types(frames)

        # ===== Step 5: 結果を構造化して返す =====
        result = {
            # 姓の文字と画数（①大: 3, ②神: 9 のような形式）
            "姓": {
                f"{chr(0x2460 + i)}{c.char}": c.strokes for i, c in enumerate(components.surname)
            },
            # 名の文字と画数（①加: 5, ②五: 4... のような形式）
            "名": {
                f"{chr(0x2460 + i)}{c.char}": c.strokes for i, c in enumerate(components.given_name)
            },
            # 七格すべての詳細情報
            "七格": {
                frame.name: {
                    "数": frame.value,            # 格の数値
                    "数霊": frame.spirit_number,  # 数霊番号（1-91）
                    "系数": frame.system_number,  # 系数（一の位）
                    "秘数": frame.secret_number,  # 秘数（数字根）
                    "系数星導": frame.system_star.split("(")[0] if frame.system_star else None,  # 系数の星導名のみ
                    "秘数星導": frame.secret_star.split("(")[0] if frame.secret_star else None,  # 秘数の星導名のみ
                    "系数星導＋象意": frame.system_star,  # 系数の星導（象意付き）
                    "秘数星導＋象意": frame.secret_star,  # 秘数の星導（象意付き）
                    "吉凶": frame.fortune,        # 吉凶判定
                    "象意": frame.meaning,        # 象意
                    "十干": frame.ten_stems,      # 十干
                    "五行": frame.five_elements   # 五行
                } for frame in frames.all_frames()
            },
            # 星導分布（10天体ごとの出現回数）
            "星導分布": star_distribution.to_dict(),
            # 人材4類型（軍人・天才・秀才・凡人の度数）
            "人材4類型": personnel_types.to_dict()
        }

        return result


def main():
    """
    直接実行時の警告とガイダンス
    """
    print("=" * 80)
    print("WARNING: Direct Execution Mode / 警告：直接実行モード")
    print("=" * 80)
    print()
    print("このスクリプトを直接実行していますが、")
    print("正確な姓名判断を行うためには以下が必要です：")
    print()
    print("1. [CLAUDE.md] の完全な理解")
    print("   場所：../CLAUDE.md（相対パス）")
    print("   内容：")
    print("   - 画数計算の詳細ルール（旧字体・新字体・異体字）")
    print("   - 身強身弱判定の理論")
    print("   - 人材4類型の判定方法")
    print("   - 軍師としての献策フレームワーク")
    print()
    print("2. 姓名の正確な確認")
    print("   - 使用する字体の確認（旧字体/新字体/異体字）")
    print("   - 各文字の画数の事前確認と合意")
    print()
    print("3. [AssessmentTemplate.md] の使用")
    print("   場所：./AssessmentTemplate.md（相対パス）")
    print("   - 標準化された出力フォーマット")
    print()
    print("=" * 80)
    print("推奨される使用方法：")
    print()
    print("1. ClaudeがCLAUDE.mdを事前に読み込み")
    print("2. Claude対話内でこのスクリプトをインポート：")
    print("   import sys")
    print("   from pathlib import Path")
    print("   # Weaveプロジェクトルートを探す（環境非依存）")
    print("   cwd = Path.cwd()")
    print("   weave_root = cwd if cwd.name == 'Weave' else next((p for p in cwd.parents if p.name == 'Weave'), cwd)")
    print("   seimei_path = weave_root / 'Expertises/CorporateStrategist/ForesightReader/Seimei'")
    print("   sys.path.append(str(seimei_path))")
    print("   from fortune_teller_assessment import FortuneTellerAssessment")
    print("3. 対話的に姓名と画数を確認")
    print("4. assess()メソッドで計算を実行")
    print("5. AssessmentTemplate.mdに結果を埋め込んで鑑定書を生成")
    print("=" * 80)
    print()
    print("このスクリプトは直接実行するものではなく、")
    print("Claudeの対話内でライブラリとしてインポートして使用します。")
    print()
    print("詳細な手順はCLAUDE.mdを参照してください。")
    print("=" * 80)


if __name__ == "__main__":
    main()


