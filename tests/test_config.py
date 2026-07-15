from pathlib import Path

import pytest

from app.config import _get_float, _get_int, write_env_values


@pytest.mark.parametrize('value', ['invalid', 'nan', 'inf', '-inf'])
def test_get_float_uses_default_for_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv('AIRCONTROL_TEST_FLOAT', value)

    result = _get_float('AIRCONTROL_TEST_FLOAT', 0.5, minimum=0.0, maximum=1.0)

    assert result == 0.5


def test_get_float_clamps_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('AIRCONTROL_TEST_FLOAT', '2.5')

    result = _get_float('AIRCONTROL_TEST_FLOAT', 0.5, minimum=0.0, maximum=1.0)

    assert result == 1.0


def test_get_int_clamps_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('AIRCONTROL_TEST_INT', '99')

    result = _get_int('AIRCONTROL_TEST_INT', 5, minimum=1, maximum=30)

    assert result == 30


def test_write_env_values_preserves_unrelated_entries_and_removes_duplicates(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / '.env'
    env_path.write_text(
        '# user setting\nUNRELATED=keep-me\nSETTING=old\nSETTING=duplicate\n',
        encoding='utf-8',
    )

    write_env_values({'SETTING': 'new', 'ADDED': 'value'}, env_path)

    assert env_path.read_text(encoding='utf-8') == (
        '# user setting\nUNRELATED=keep-me\nSETTING=new\n\nADDED=value\n'
    )
