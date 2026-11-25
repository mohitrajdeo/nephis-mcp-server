"""
Eschaton Python SDK: Sub-38ms Untrusted Code Execution, In-Memory AST Safety,
and 10 Evaluation Suites for Competitive Programming, AI Agents, and Educational Platforms.
"""

import json
import os
import ssl
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

try:
    _DEFAULT_SSL_CTX = ssl._create_unverified_context()
except Exception:
    _DEFAULT_SSL_CTX = ssl.create_default_context()
    _DEFAULT_SSL_CTX.check_hostname = False
    _DEFAULT_SSL_CTX.verify_mode = ssl.CERT_NONE


class EschatonError(Exception):
    """Base exception for all Eschaton API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class EschatonClient:
    """Dedicated high-throughput code execution and assessment client.
    
    Provides direct access to:
      - Sub-38ms synchronous code execution across 60+ compilers
      - 10 architectural evaluation suites (Omni, Apex, Void, Complexity, Sanitizer, etc.)
      - AST preflight safety analysis (<50µs)
      - Ephemeral DBMS schema injection and custom competitive programming checkers
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        env_url = os.environ.get("ESCHATON_GATEWAY_URL") or os.environ.get("NEPHIS_BASE_URL") or "https://nephis.theeducode.com"
        self.base_url = (base_url or env_url).rstrip("/")
        self.api_key = (
            api_key
            or os.environ.get("ESCHATON_API_KEY")
            or os.environ.get("NEPHIS_API_KEY")
        )
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        if not self.api_key:
            raise EschatonError("Set ESCHATON_API_KEY or pass api_key when creating EschatonClient.")
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; Eschaton-Python-SDK/1.0)",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
        }
        if method.upper() == "POST" and path in ("/v1/execute", "/v1/submissions/fast-batch"):
            headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())

        last_error = None
        for attempt in range(3):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=_DEFAULT_SSL_CTX) as resp:
                    resp_bytes = resp.read()
                    return json.loads(resp_bytes.decode("utf-8")) if resp_bytes else {}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                last_error = EschatonError(f"Eschaton API error [{e.code}]: {err_body}", status_code=e.code, response_body=err_body)
                if e.code in (502, 503, 504) and attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error from e
            except urllib.error.URLError as e:
                last_error = EschatonError(f"Failed to connect to Eschaton engine at {url}: {e.reason}")
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error from e

    def execute(
        self,
        source_code: str,
        language_id: int = 71,
        stdin: str = "",
        expected_output: Optional[str] = None,
        suite: str = "Apex",  # Omni is deprecated/degraded; default to Apex
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a single code submission synchronously in <38ms."""
        tc = {"id": 1, "stdin": stdin}
        if expected_output is not None:
            tc["expected_output"] = expected_output
        return self.execute_suite(
            source_code=source_code,
            language_id=language_id,
            suite=suite,
            test_cases=[tc],
            idempotency_key=idempotency_key,
        )

    def execute_suite(
        self,
        source_code: str,
        language_id: int = 71,
        suite: str = "Apex",  # Omni is deprecated/degraded; default to Apex
        test_cases: Optional[List[Dict[str, Any]]] = None,
        database: Optional[str] = None,
        checker_code: Optional[str] = None,
        checker_language_id: Optional[int] = None,
        verbose: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch submission against any of the Eschaton assessment suites:
        Apex (default, multi-core cgroups v2), Void (sub-4ms in-memory microkernel), Complexity, Sanitizer, MemoryProfile, FileIO, DBMS, SpecialJudge.
        Note: Omni suite is deprecated/degraded due to single-case EOF pipe termination.
        """
        payload: Dict[str, Any] = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": suite,
            "test_cases": test_cases or [{"id": 1, "stdin": "", "expected_output": ""}],
        }
        if database:
            payload["database"] = database
        if checker_code:
            payload["checker_code"] = checker_code
            payload["checker_language_id"] = checker_language_id or language_id
        if verbose is not None:
            payload["verbose"] = verbose
        return self._request("POST", "/v1/execute", body=payload, idempotency_key=idempotency_key)

    def batch_execute(
        self,
        source_code: str,
        tests: List[Dict[str, Any]],
        suite: str = "Apex",  # Omni is deprecated/degraded; default to Apex
        language_id: int = 54,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """High-throughput parallel testcase matrix execution."""
        return self.execute_suite(
            source_code=source_code,
            language_id=language_id,
            suite=suite,
            test_cases=tests,
            idempotency_key=idempotency_key,
        )

    def complexity_profile(
        self,
        source_code: str,
        language_id: int = 202,
        stdin: str = "100",
    ) -> Dict[str, Any]:
        """Algorithmic instruction count & Big-O verification via Valgrind lackey."""
        return self.execute_suite(
            source_code=source_code,
            language_id=language_id,
            suite="Complexity",
            test_cases=[{"id": 1, "stdin": stdin}],
        )

    def sanitize_check(
        self,
        source_code: str,
        language_id: int = 202,
        stdin: str = "",
    ) -> Dict[str, Any]:
        """Sub-20ms AddressSanitizer (ASan) + UBSan memory safety & leak audit."""
        return self.execute_suite(
            source_code=source_code,
            language_id=language_id,
            suite="Sanitizer",
            test_cases=[{"id": 1, "stdin": stdin}],
        )

    def dbms_eval(
        self,
        source_code: str,
        schema_sql: str = "",
        database: str = "sqlite",
        expected_output: Optional[str] = None,
        stdin: str = "",
    ) -> Dict[str, Any]:
        """Automated SQL query assessment across SQLite, PostgreSQL, MySQL, and Oracle."""
        # If pure SQL is passed for SQLite, wrap it in a lightweight runner
        if database == "sqlite" and not ("import sqlite3" in source_code or "def " in source_code):
            actual_source = (
                "import sqlite3\n"
                "conn = sqlite3.connect(':memory:')\n"
                f"schema = {schema_sql!r}\n"
                "if schema:\n"
                "    conn.executescript(schema)\n"
                f"query = {source_code!r}\n"
                "for row in conn.execute(query):\n"
                "    print('|'.join(str(c) for c in row))\n"
            )
        else:
            actual_source = source_code

        tc: Dict[str, Any] = {"id": 1, "schema_sql": schema_sql, "stdin": stdin}
        if expected_output:
            tc["expected_output"] = expected_output
        payload = {
            "language_id": 204,
            "source_code": actual_source,
            "suite": "DBMS",
            "database": database,
            "test_cases": [tc],
        }
        res = self._request("POST", "/v1/execute", body=payload, idempotency_key=None)
        # Normalize if gateway returns top-level execution result or Results array
        if "Results" not in res and "stdout" in res:
            res["Results"] = [{
                "test_case_id": 1,
                "passed": res.get("exit_code", 1) == 0,
                "stdout": res.get("stdout", ""),
                "stderr": res.get("stderr", ""),
                "time": res.get("time", 0),
                "schema_applied": True,
            }]
        return res

    def fileio_eval(
        self,
        source_code: str,
        input_filename: str = "input.txt",
        input_content: str = "DATA",
        output_filename: str = "output.txt",
        expected_output: Optional[str] = None,
        language_id: int = 204,
    ) -> Dict[str, Any]:
        """Isolated filesystem sandbox grading with custom input and output files."""
        tc: Dict[str, Any] = {
            "id": 1,
            "files": {input_filename: input_content},
            "output_file": output_filename,
        }
        if expected_output:
            tc["expected_output"] = expected_output
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "FileIO",
            "test_cases": [tc],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def special_judge(
        self,
        source_code: str,
        checker_code: str,
        language_id: int = 202,
        checker_language_id: int = 202,
        stdin: str = "5.0",
        expected_output: str = "2.5",
    ) -> Dict[str, Any]:
        """Custom competitive programming checker binary validator."""
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "SpecialJudge",
            "checker_code": checker_code,
            "checker_language_id": checker_language_id,
            "test_cases": [{"id": 1, "stdin": stdin, "expected_output": expected_output}],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def list_languages(self) -> List[Dict[str, Any]]:
        """Retrieve 60+ supported compiler runtimes and version manifests."""
        try:
            return self._request("GET", "/v1/languages")
        except Exception:
            return self._request("GET", "/languages")

    def preflight_check(self, source_code: str, language_id: int = 71) -> Dict[str, Any]:
        """Execute sub-50µs in-memory AST syntax safety verification."""
        payload = {"source_code": source_code, "language_id": language_id}
        return self._request("POST", "/v1/execute/preflight", body=payload)

    def get_quota(self) -> Dict[str, Any]:
        """Inspect active key quota, rate limits, and remaining balance."""
        return self._request("GET", "/v1/account")
