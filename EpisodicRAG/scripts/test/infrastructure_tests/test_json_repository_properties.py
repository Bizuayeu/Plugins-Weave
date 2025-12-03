#!/usr/bin/env python3
"""
Property-Based Tests for JSON Repository
=========================================

Testing JSON I/O roundtrip invariants.
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from infrastructure.json_repository import (
    load_json,
    save_json,
    try_load_json,
)

# =============================================================================
# Strategies for JSON-serializable data
# =============================================================================

# Simple JSON dicts (avoid complex recursive structures for speed)
simple_json_dicts = st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.text(max_size=50),
    ),
    max_size=5,
)


# =============================================================================
# Roundtrip Properties
# =============================================================================


class TestJsonRoundtripProperties:
    """Test save/load roundtrip properties"""

    @pytest.mark.property
    @pytest.mark.integration
    @given(data=simple_json_dicts)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_save_load_roundtrip(self, data) -> None:

        """Any JSON-serializable dict survives save/load roundtrip"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "test.json"

            save_json(file_path, data)
            loaded = load_json(file_path)

            assert loaded == data

    @pytest.mark.property
    @pytest.mark.integration
    @given(data=simple_json_dicts)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_save_preserves_unicode(self, data) -> None:

        """Unicode characters are preserved in roundtrip"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Add unicode content to data
            unicode_data = {"japanese": "こんにちは", "korean": "안녕하세요", "emoji": "🎉", **data}
            file_path = Path(tmp_dir) / "unicode.json"

            save_json(file_path, unicode_data)
            loaded = load_json(file_path)

            assert loaded["japanese"] == "こんにちは"
            assert loaded["korean"] == "안녕하세요"
            assert loaded["emoji"] == "🎉"


# =============================================================================
# try_load_json Properties
# =============================================================================


class TestTryLoadJsonProperties:
    """Test try_load_json never raises"""

    @pytest.mark.property
    @pytest.mark.integration
    @given(default=simple_json_dicts)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_returns_default_for_missing_file(self, default) -> None:

        """try_load_json returns default for missing file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "nonexistent.json"

            result = try_load_json(missing, default=default)

            assert result == default

    @pytest.mark.property
    @pytest.mark.integration
    def test_never_raises_on_invalid_json(self) -> None:

        """try_load_json returns default for truly invalid JSON content"""
        invalid_contents = [
            "not json at all",
            "{invalid: json}",
            "{'single': 'quotes'}",
            "{missing: closing",
            "random text here",
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            default = {"fallback": True}
            for i, content in enumerate(invalid_contents):
                file_path = Path(tmp_dir) / f"invalid_{i}.json"
                file_path.write_text(content, encoding='utf-8')

                # Should not raise
                result = try_load_json(file_path, default=default)

                # Should return default for invalid JSON
                assert result == default, f"Failed for content: {content}"

    @pytest.mark.property
    @pytest.mark.integration
    @given(data=simple_json_dicts)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow], deadline=1000)
    def test_returns_data_for_valid_file(self, data) -> None:

        """try_load_json returns data for valid file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "valid.json"
            save_json(file_path, data)

            result = try_load_json(file_path, default={"default": True})

            assert result == data


# =============================================================================
# Edge Cases
# =============================================================================


class TestJsonEdgeCases:
    """Test edge cases in JSON handling"""

    @pytest.mark.property
    @pytest.mark.integration
    def test_empty_dict_roundtrip(self, tmp_path: Path) -> None:

        """Empty dict survives roundtrip"""
        file_path = tmp_path / "empty.json"

        save_json(file_path, {})
        loaded = load_json(file_path)

        assert loaded == {}

    @pytest.mark.property
    @pytest.mark.integration
    @given(
        key=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        value=st.one_of(st.integers(), st.text(max_size=50), st.booleans(), st.none()),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_single_key_value_roundtrip(self, key, value) -> None:

        """Single key-value pair survives roundtrip"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "single.json"
            data = {key: value}

            save_json(file_path, data)
            loaded = load_json(file_path)

            assert loaded == data

    @pytest.mark.property
    @pytest.mark.integration
    @given(depth=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def test_nested_dict_roundtrip(self, depth) -> None:

        """Nested dicts survive roundtrip"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create nested structure
            data = {"level": 0}
            current = data
            for i in range(1, depth + 1):
                current["nested"] = {"level": i}
                current = current["nested"]

            file_path = Path(tmp_dir) / "nested.json"
            save_json(file_path, data)
            loaded = load_json(file_path)

            assert loaded == data

    @pytest.mark.property
    @pytest.mark.integration
    @given(indent=st.integers(min_value=0, max_value=8))
    @settings(max_examples=20)
    def test_different_indents(self, indent) -> None:

        """Different indent values work correctly"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "indented.json"
            data = {"key": "value", "nested": {"inner": "data"}}

            save_json(file_path, data, indent=indent)
            loaded = load_json(file_path)

            assert loaded == data
