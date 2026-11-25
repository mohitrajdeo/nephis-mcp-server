import sys
from pathlib import Path
tests_dir = Path(__file__).resolve().parent
sdk_dir = tests_dir.parent
sys.path.insert(0, str(sdk_dir))
sys.path.insert(0, str(tests_dir))

from unittest.mock import patch
from eschaton import EschatonClient, EschatonError
from live_config import NEPHIS_URL, get_live_api_key


def test_eschaton_init():
    client = EschatonClient(base_url=NEPHIS_URL, api_key="esk_test_123")
    assert client.base_url == NEPHIS_URL
    assert client.api_key == "esk_test_123"


def test_eschaton_execute():
    api_key = get_live_api_key()
    client = EschatonClient(base_url=NEPHIS_URL, api_key=api_key)

    res = client.execute("print('LIVE_ESCHATON_PY_PASS')", language_id=204)
    assert len(res["Results"]) >= 1
    assert res["Results"][0]["passed"] is True
    assert "LIVE_ESCHATON_PY_PASS" in res["Results"][0]["stdout"]


def test_eschaton_complexity_and_sanitizer():
    api_key = get_live_api_key()
    client = EschatonClient(base_url=NEPHIS_URL, api_key=api_key)

    # Real Valgrind instruction profiling on GCC 14 C++
    comp = client.complexity_profile("int main(){ return 0; }", language_id=202)
    assert len(comp["Results"]) >= 1
    assert comp["Results"][0]["passed"] is True
    instructions = comp["Results"][0].get("instructions_executed") or comp["Results"][0].get("time")
    assert int(instructions) > 1000

    # Real AddressSanitizer check on GCC 14 C++
    san = client.sanitize_check("int main(){ return 0; }", language_id=202)
    assert len(san["Results"]) >= 1
    assert "ASan" in san["Results"][0]["stderr"] or san["Results"][0]["passed"] is True


def test_eschaton_dbms_and_fileio():
    api_key = get_live_api_key()
    client = EschatonClient(base_url=NEPHIS_URL, api_key=api_key)

    # Real Ephemeral SQLite DBMS evaluation
    db = client.dbms_eval(
        source_code="SELECT * FROM students WHERE score > 80;",
        schema_sql="CREATE TABLE students(id INT, name TEXT, score INT); INSERT INTO students VALUES (1, 'Arun', 95), (2, 'Bala', 72);",
        database="sqlite"
    )
    assert len(db.get("Results", [])) >= 1
    assert db["Results"][0]["passed"] is True
    assert "Arun" in db["Results"][0]["stdout"]

    # Real Sandboxed FileIO verification
    fileio = client.fileio_eval(
        source_code="with open('in.txt') as f:\n    val = f.read().strip()\nwith open('out.txt', 'w') as f:\n    f.write(f'PROCESSED_{val}')",
        input_filename="in.txt",
        input_content="2026",
        output_filename="out.txt",
        expected_output="PROCESSED_2026",
        language_id=204
    )
    assert len(fileio.get("Results", [])) >= 1
    assert fileio["Results"][0]["passed"] is True


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
