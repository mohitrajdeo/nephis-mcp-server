export class ThanatonError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ThanatonError";
  }
}

export class ThanatonAPIError extends ThanatonError {
  constructor(public statusCode: number, public responseBody: string) {
    super(`Thanaton API error [HTTP ${statusCode}]: ${responseBody}`);
    this.name = "ThanatonAPIError";
  }
}

export class ThanatonTimeoutError extends ThanatonError {
  constructor(public timeoutMs: number, path: string) {
    super(`Thanaton request timeout after ${timeoutMs}ms: ${path}`);
    this.name = "ThanatonTimeoutError";
  }
}

export class ThanatonRateLimitError extends ThanatonError {
  constructor(public retryAfterSeconds: number, message: string) {
    super(`Thanaton rate limit exceeded: ${message} (retry after ${retryAfterSeconds}s)`);
    this.name = "ThanatonRateLimitError";
  }
}

export class ThanatonCapacityError extends ThanatonError {
  constructor(message: string) {
    super(`Thanaton capacity saturated: ${message}. Recommendation: Retry with exponential backoff.`);
    this.name = "ThanatonCapacityError";
  }
}

export class EschatonFuelExhaustedError extends ThanatonError {
  constructor(message: string) {
    super(`Eschaton gas/fuel budget exhausted: ${message}. Recommendation: Optimize computational complexity.`);
    this.name = "EschatonFuelExhaustedError";
  }
}

export class ThanatonConnectionError extends ThanatonError {
  constructor(public url: string, public reason: string) {
    super(
      `Cannot connect to Thanaton Daemon at ${url} (${reason}).\n` +
      "  -> If running locally: Launch the daemon with 'ananked' or 'python scripts/ananked.py'\n" +
      "  -> If using managed cloud: Set baseUrl='https://nephis.theeducode.com/pricing' and apiKey='sk_live_...'\n" +
      "  -> Quickstart guide: https://nephis.theeducode.com/docs"
    );
    this.name = "ThanatonConnectionError";
  }
}

export class EscalationRequiredError extends ThanatonError {
  constructor(
    public capability: string,
    public attempted: string,
    public reason: string,
    public upgradeCode: string = "const sandbox = await client.upgradeToThanaton(session)",
    public serializedState: Record<string, any> = {}
  ) {
    super(
      `EscalationRequired [${capability}]: Attempted \`${attempted}\` (${reason}). ` +
      `Upgrade to Thanaton MicroVM using: \`${upgradeCode}\``
    );
    this.name = "EscalationRequiredError";
  }
}

