"""Tests for infrastructure/file_io."""

from pathlib import Path

from scripts.infrastructure.file_io import read_json_safe, write_json_atomic


class TestWriteJsonAtomic:
    def test_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        data: dict[str, object] = {"key": "value", "num": 42}
        write_json_atomic(path, data)
        result = read_json_safe(path)
        assert result is not None
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        write_json_atomic(path, {"v": 1})
        write_json_atomic(path, {"v": 2})
        result = read_json_safe(path)
        assert result is not None
        assert result["v"] == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / "test.json"
        write_json_atomic(path, {"ok": True})
        result = read_json_safe(path)
        assert result is not None
        assert result["ok"] is True

    def test_unicode_content(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        write_json_atomic(path, {"label": "落ち着き"})
        result = read_json_safe(path)
        assert result is not None
        assert result["label"] == "落ち着き"


class TestReadJsonSafe:
    def test_missing_file(self, tmp_path: Path) -> None:
        result = read_json_safe(tmp_path / "nonexistent.json")
        assert result is None

    def test_corrupt_json(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not json!", encoding="utf-8")
        assert read_json_safe(path) is None

    def test_non_dict_json(self, tmp_path: Path) -> None:
        path = tmp_path / "array.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        assert read_json_safe(path) is None
