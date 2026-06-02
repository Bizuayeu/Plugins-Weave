"""exit code SSoT の契約 pin（Stage 2）。

値は外部契約（SKILL.md / ROUTINE_PROMPT.md / SECURITY.md / bootstrap.sh）なので、
うっかり変えたら赤になるよう各値を固定し、main からの re-export 後方互換も検証する。
"""
from __future__ import annotations

from infrastructure.exit_codes import (
    EXIT_AUTH_FAILED,
    EXIT_CONFIG_INVALID,
    EXIT_FETCH_FAILED,
    EXIT_LEASE_CONFLICT,
    EXIT_OK,
)


def test_exit_code_values_are_stable_contract():
    """0/1/2/3/4 は公開契約。SKILL.md/ROUTINE_PROMPT.md/SECURITY.md と一致させる。"""
    assert EXIT_OK == 0
    assert EXIT_FETCH_FAILED == 1
    assert EXIT_CONFIG_INVALID == 2
    assert EXIT_AUTH_FAILED == 3
    assert EXIT_LEASE_CONFLICT == 4


def test_main_reexports_exit_codes_for_backward_compat():
    """main は exit_codes を re-export する（`from main import EXIT_*` を割らない）。"""
    import main

    assert main.EXIT_OK is EXIT_OK
    assert main.EXIT_FETCH_FAILED is EXIT_FETCH_FAILED
    assert main.EXIT_CONFIG_INVALID is EXIT_CONFIG_INVALID
    assert main.EXIT_AUTH_FAILED is EXIT_AUTH_FAILED
    assert main.EXIT_LEASE_CONFLICT is EXIT_LEASE_CONFLICT
