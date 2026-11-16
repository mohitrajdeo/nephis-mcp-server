import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch, MagicMock
from eschaton import EschatonClient, EschatonError


def test_eschaton_init():
    client = EschatonClient(base_url="https://compiler.theeducode.com", api_key="esk_test_123")
    assert client.base_url == "https://compiler.theeducode.com"
    assert client.api_key == "esk_test_123"


@patch("urllib.request.urlopen")
def test_eschaton_execute(mock_urlopen):
    client = EschatonClient(base_url="https://compiler.theeducode.com", api_key="esk_test_123")

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"Results":[{"test_case_id":1,"time":0.019,"passed":true,"stdout":"OK"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = client.execute("print('OK')", language_id=71)
    assert len(res["Results"]) == 1
    assert res["Results"][0]["passed"] is True
    assert res["Results"][0]["stdout"] == "OK"


@patch("urllib.request.urlopen")
def test_eschaton_complexity_and_sanitizer(mock_urlopen):
    client = EschatonClient(base_url="https://compiler.theeducode.com", api_key="esk_test_123")

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"Results":[{"test_case_id":1,"passed":true,"instructions_executed":15000}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    comp = client.complexity_profile("int main(){}", language_id=202)
    assert comp["Results"][0]["instructions_executed"] == 15000


@patch("urllib.request.urlopen")
def test_eschaton_dbms_and_fileio(mock_urlopen):
    client = EschatonClient(base_url="https://compiler.theeducode.com", api_key="esk_test_123")

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"Results":[{"test_case_id":1,"passed":true,"schema_applied":true}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    db = client.dbms_eval("SELECT 1;", schema_sql="CREATE TABLE t(x int);", database="sqlite")
    assert db["Results"][0]["schema_applied"] is True


def test_eschaton_cli_help(capsys):
    from eschaton.cli import main
    import pytest

    with patch("sys.argv", ["eschatonctl", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "eschatonctl" in captured.out


def test_eschaton_cli_man(capsys):
    from eschaton.cli import main
    with patch("sys.argv", ["eschatonctl", "man"]):
        main()
    captured = capsys.readouterr()
    assert "ESCHATONCTL(1)" in captured.out
