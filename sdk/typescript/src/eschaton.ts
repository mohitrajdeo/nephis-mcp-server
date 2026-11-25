/**
 * Eschaton TypeScript SDK - High-Throughput Stateless Code Execution & Assessment Client
 *
 * Provides native bindings for:
 *  - Sub-38ms synchronous untrusted code execution across 60+ compilers
 *  - 10 architectural evaluation suites (Omni, Apex, Void, Complexity, Sanitizer, etc.)
 *  - AST preflight safety checks (<50µs)
 *  - Parallel batch testing matrices and custom competitive programming checkers
 */

import type {
  ExecuteSuiteOptions,
  ExecuteSuiteResult,
  ComplexityProfileOptions,
  ComplexityProfileResult,
  SanitizeCheckOptions,
  SanitizeCheckResult,
  DBMSEvalOptions,
  DBMSEvalResult,
  FileIOEvalOptions,
  FileIOEvalResult,
  SpecialJudgeOptions,
  SpecialJudgeResult,
  BatchExecuteOptions,
  BatchExecuteResult,
  TestCaseSpec,
} from "./types.js";

declare const process: any;

export interface EschatonClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeoutMs?: number;
}

export class EschatonError extends Error {
  constructor(message: string, public statusCode?: number, public responseBody?: string) {
    super(message);
    this.name = "EschatonError";
  }
}

export class EschatonClient {
  public baseUrl: string;
  public apiKey: string;
  public timeoutMs: number;

  constructor(options: EschatonClientOptions = {}) {
    const envUrl = typeof process !== "undefined" && process.env
      ? (process.env.ESCHATON_GATEWAY_URL || process.env.NEPHIS_BASE_URL)
      : undefined;
    const envKey = typeof process !== "undefined" && process.env
      ? (process.env.ESCHATON_API_KEY || process.env.NEPHIS_API_KEY)
      : undefined;

    this.baseUrl = (options.baseUrl || envUrl || "https://nephis.theeducode.com").replace(/\/+$/, "");
    this.apiKey = options.apiKey || envKey || "";
    this.timeoutMs = options.timeoutMs || 60000;
  }

  private async request<T = any>(method: string, path: string, body?: any, extraHeaders: Record<string, string> = {}): Promise<T> {
    if (!this.apiKey) {
      throw new EschatonError("Set ESCHATON_API_KEY or pass apiKey when creating EschatonClient.");
    }
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
      headers["X-API-Key"] = this.apiKey;
    }
    if (method.toUpperCase() === "POST" && path === "/v1/execute" && !extraHeaders["Idempotency-Key"]) {
      extraHeaders = { ...extraHeaders, "Idempotency-Key": crypto.randomUUID() };
    }
    Object.assign(headers, extraHeaders);

    let lastError: any = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

      try {
        const res = await fetch(url, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        if (!res.ok) {
          // Fallback from /v1/execute to /execute if 404/405
          if ((res.status === 404 || res.status === 405) && path === "/v1/execute") {
            clearTimeout(timeout);
            return this.request<T>(method, "/execute", body, extraHeaders);
          }
          const errText = await res.text();
          if ([502, 503, 504].includes(res.status) && attempt < 2) {
            clearTimeout(timeout);
            await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
            continue;
          }
          throw new EschatonError(`Eschaton API error [HTTP ${res.status}]: ${errText}`, res.status, errText);
        }

        return await res.json();
      } catch (err: any) {
        lastError = err;
        if (err instanceof EschatonError) {
          throw err;
        }
        if (attempt < 2 && (err.name === "TypeError" || err.name === "AbortError" || err.message?.includes("fetch failed") || err.message?.includes("aborted"))) {
          await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
          continue;
        }
        throw err;
      } finally {
        clearTimeout(timeout);
      }
    }
    throw lastError;
  }

  /**
   * Run a single code execution synchronously in <38ms.
   */
  async execute(params: {
    sourceCode?: string;
    source_code?: string;
    languageId?: number;
    language_id?: number;
    stdin?: string;
    expectedOutput?: string;
    expected_output?: string;
    suite?: string;
    idempotencyKey?: string;
  }): Promise<ExecuteSuiteResult> {
    const resolvedCode = params.sourceCode || params.source_code || "";
    const resolvedLang = params.languageId ?? params.language_id ?? 71;
    const tc: TestCaseSpec = { id: 1, stdin: params.stdin ?? "" };
    if (params.expectedOutput !== undefined) {
      tc.expected_output = params.expectedOutput;
    } else if (params.expected_output !== undefined) {
      tc.expected_output = params.expected_output;
    }
    return this.executeSuite({
      sourceCode: resolvedCode,
      languageId: resolvedLang,
      suite: params.suite ?? "Apex",
      testCases: [tc],
      idempotencyKey: params.idempotencyKey,
    });
  }

  /**
   * Dispatch against any of Eschaton's assessment suites:
   * Apex (hard-isolated multi-core, default), Void (sub-4ms in-memory microkernel),
   * Complexity, Sanitizer, MemoryProfile, FileIO, DBMS, SpecialJudge. (Omni is deprecated).
   */
  async executeSuite(params: ExecuteSuiteOptions & { source_code?: string; language_id?: number; test_cases?: TestCaseSpec[] }): Promise<ExecuteSuiteResult> {
    const resolvedCode = params.sourceCode || params.source_code || "";
    const resolvedLang = params.languageId ?? params.language_id ?? 71;
    const resolvedCases = params.testCases || params.test_cases;
    const payload: Record<string, any> = {
      language_id: resolvedLang,
      source_code: resolvedCode,
      suite: params.suite ?? "Apex",
      test_cases: resolvedCases && resolvedCases.length > 0
        ? resolvedCases
        : [{ id: 1, stdin: "", expected_output: "" }],
    };
    if (params.database) payload.database = params.database;
    if (params.checkerCode) {
      payload.checker_code = params.checkerCode;
      payload.checker_language_id = params.checkerLanguageId ?? resolvedLang;
    }
    if (params.verbose !== undefined) payload.verbose = params.verbose;
    const requestHeaders: Record<string, string> = params.idempotencyKey ? { "Idempotency-Key": params.idempotencyKey } : {};
    return this.request<ExecuteSuiteResult>("POST", "/v1/execute", payload, requestHeaders);
  }

  /**
   * High-throughput parallel testcase matrix execution.
   */
  async batchExecute(params: BatchExecuteOptions & { source_code?: string; language_id?: number; test_cases?: any[] }): Promise<BatchExecuteResult> {
    const resolvedCode = params.sourceCode || params.source_code || "";
    const resolvedLang = params.languageId ?? params.language_id ?? 54;
    const resolvedTests = params.tests || params.test_cases || [];
    const payload = {
      language_id: resolvedLang,
      source_code: resolvedCode,
      suite: params.suite ?? "Apex",
      test_cases: resolvedTests,
    };
    const requestHeaders: Record<string, string> = params.idempotencyKey ? { "Idempotency-Key": params.idempotencyKey } : {};
    return this.request<BatchExecuteResult>("POST", "/v1/execute", payload, requestHeaders);
  }

  /**
   * Algorithmic instruction count & Big-O verification via Valgrind lackey.
   */
  async complexityProfile(params: ComplexityProfileOptions): Promise<ComplexityProfileResult> {
    const payload = {
      language_id: params.languageId ?? 202,
      source_code: params.sourceCode,
      suite: "Complexity",
      test_cases: [{ id: 1, stdin: params.stdin ?? "100" }],
    };
    return this.request<ComplexityProfileResult>("POST", "/v1/execute", payload);
  }

  /**
   * Sub-20ms AddressSanitizer (ASan) + UBSan memory safety audit.
   */
  async sanitizeCheck(params: SanitizeCheckOptions): Promise<SanitizeCheckResult> {
    const payload = {
      language_id: params.languageId ?? 202,
      source_code: params.sourceCode,
      suite: "Sanitizer",
      test_cases: [{ id: 1, stdin: params.stdin ?? "" }],
    };
    return this.request<SanitizeCheckResult>("POST", "/v1/execute", payload);
  }

  /**
   * Automated SQL database grading with ephemeral schema injection across SQLite, Postgres, MySQL, Oracle.
   */
  async dbmsEval(params: DBMSEvalOptions): Promise<DBMSEvalResult> {
    const tc: Record<string, any> = {
      id: 1,
      schema_sql: params.schemaSql,
      stdin: params.stdin ?? "",
    };
    if (params.expectedOutput) tc.expected_output = params.expectedOutput;
    const payload = {
      language_id: 204,
      source_code: params.sourceCode,
      suite: "DBMS",
      database: params.database ?? "sqlite",
      test_cases: [tc],
    };
    return this.request<DBMSEvalResult>("POST", "/v1/execute", payload);
  }

  /**
   * Isolated filesystem sandbox grading with custom input and output files.
   */
  async fileioEval(params: FileIOEvalOptions): Promise<FileIOEvalResult> {
    const inputFilename = params.inputFilename ?? "input.txt";
    const inputContent = params.inputContent ?? "DATA";
    const outputFilename = params.outputFilename ?? "output.txt";
    const tc: Record<string, any> = {
      id: 1,
      files: { [inputFilename]: inputContent },
      output_file: outputFilename,
    };
    if (params.expectedOutput) tc.expected_output = params.expectedOutput;
    const payload = {
      language_id: params.languageId ?? 204,
      source_code: params.sourceCode,
      suite: "FileIO",
      test_cases: [tc],
    };
    return this.request<FileIOEvalResult>("POST", "/v1/execute", payload);
  }

  /**
   * Custom competitive programming checker binary validator.
   */
  async specialJudge(params: SpecialJudgeOptions): Promise<SpecialJudgeResult> {
    const payload = {
      language_id: params.languageId ?? 202,
      source_code: params.sourceCode,
      suite: "SpecialJudge",
      checker_code: params.checkerCode,
      checker_language_id: params.checkerLanguageId ?? params.languageId ?? 202,
      test_cases: [
        {
          id: 1,
          stdin: params.stdin ?? "5.0",
          expected_output: params.expectedOutput ?? "2.5",
        },
      ],
    };
    return this.request<SpecialJudgeResult>("POST", "/v1/execute", payload);
  }

  /**
   * List supported compilers and version manifests.
   */
  async listLanguages(): Promise<any[]> {
    try {
      return await this.request("GET", "/v1/languages");
    } catch {
      return await this.request("GET", "/languages");
    }
  }

  /**
   * Execute sub-50µs in-memory AST syntax safety verification.
   */
  async preflightCheck(sourceCode: string, languageId: number = 71): Promise<any> {
    return this.request("POST", "/v1/execute/preflight", { source_code: sourceCode, language_id: languageId });
  }

  /**
   * Fetch active API key quota and remaining credits.
   */
  async getQuota(): Promise<any> {
    return this.request("GET", "/v1/account");
  }
}
