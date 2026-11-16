/**
 * Nephis Cryptographic License & Authority Engine (TypeScript / Node.js)
 *
 * Provides offline cryptographic signature verification, tier entitlement checks,
 * and quota enforcement across the Nephis CLI, MCP Server, and TypeScript SDK.
 */

import * as crypto from "node:crypto";
import type { NephisTier, LicenseStatus } from "./types.js";

export const DEFAULT_LICENSE_SECRET = "ananke_enterprise_signing_secret_prod_2026";

export interface TierEntitlements {
  max_sandboxes: number;
  max_cdc_events_per_day: number;
  max_webhooks_per_day: number;
  max_pool_connections: number;
  max_pipe_gb_per_month: number;
  max_dns_qps: number;
  ebpf_sockmap_allowed: boolean;
  tcp_repair_allowed: boolean;
  features: string[];
}

export const TIERS: Record<NephisTier, TierEntitlements> = {
  community: {
    max_sandboxes: 5,
    max_cdc_events_per_day: 1000000,
    max_webhooks_per_day: 10000,
    max_pool_connections: 20,
    max_pipe_gb_per_month: 50,
    max_dns_qps: 50000,
    ebpf_sockmap_allowed: false,
    tcp_repair_allowed: false,
    features: ["sandboxes", "cdc_basic", "webhooks_basic", "pool_basic", "pipe_basic", "dns_basic"],
  },
  pro: {
    max_sandboxes: 100,
    max_cdc_events_per_day: 50000000,
    max_webhooks_per_day: 500000,
    max_pool_connections: 500,
    max_pipe_gb_per_month: 5000,
    max_dns_qps: 500000,
    ebpf_sockmap_allowed: true,
    tcp_repair_allowed: true,
    features: [
      "sandboxes",
      "cdc_pro",
      "webhooks_pro",
      "finops",
      "flight_recorder",
      "chaos",
      "pool_pro",
      "pipe_pro",
      "rootfs",
      "dns_pro",
      "live_migration",
    ],
  },
  enterprise: {
    max_sandboxes: 999999,
    max_cdc_events_per_day: 999999999999,
    max_webhooks_per_day: 999999999999,
    max_pool_connections: 999999,
    max_pipe_gb_per_month: 999999999999,
    max_dns_qps: 999999999999,
    ebpf_sockmap_allowed: true,
    tcp_repair_allowed: true,
    features: ["*"],
  },
};

export class LicenseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "LicenseError";
  }
}

export interface LicenseClaims {
  iss: string;
  tid: string;
  tier: NephisTier;
  iat: number;
  exp: number;
  ent: TierEntitlements;
}

export interface GenerateLicenseOptions {
  tenantId: string;
  tier?: NephisTier;
  expiresInDays?: number;
  secret?: string;
}

export class LicenseToken {
  /**
   * Generate a cryptographically signed HMAC-SHA256 license token string.
   */
  static generate(options: GenerateLicenseOptions): string {
    const tier = options.tier || "community";
    if (!TIERS[tier]) {
      throw new LicenseError(`Unknown tier: ${tier}`);
    }

    const secret = options.secret || DEFAULT_LICENSE_SECRET;
    const issuedAt = Math.floor(Date.now() / 1000);
    const expiresInDays = options.expiresInDays ?? 365;
    const expiresAt = issuedAt + expiresInDays * 86400;

    const claims: LicenseClaims = {
      iss: "nephis-authority",
      tid: options.tenantId,
      tier,
      iat: issuedAt,
      exp: expiresAt,
      ent: TIERS[tier],
    };

    // Sort keys deterministically
    const sortedKeys = Object.keys(claims).sort() as (keyof LicenseClaims)[];
    const orderedClaims: Record<string, any> = {};
    for (const key of sortedKeys) {
      orderedClaims[key] = claims[key];
    }

    const rawJson = Buffer.from(JSON.stringify(orderedClaims), "utf-8");
    const b64Payload = rawJson.toString("base64url");

    const hmac = crypto.createHmac("sha256", secret);
    hmac.update(b64Payload);
    const sig = hmac.digest("hex");

    return `ank_lic_${b64Payload}.${sig}`;
  }

  /**
   * Cryptographically verify an HMAC-SHA256 license token string.
   */
  static verify(token: string, secret: string = DEFAULT_LICENSE_SECRET): LicenseClaims {
    if (!token || !token.startsWith("ank_lic_")) {
      throw new LicenseError("Invalid license token format. Must start with 'ank_lic_'");
    }

    const tokenBody = token.slice("ank_lic_".length);
    const dotIndex = tokenBody.lastIndexOf(".");
    if (dotIndex === -1) {
      throw new LicenseError("Malformed license token: missing signature delimiter.");
    }

    const payloadB64 = tokenBody.slice(0, dotIndex);
    const sig = tokenBody.slice(dotIndex + 1);

    // Compute expected signature
    const hmac = crypto.createHmac("sha256", secret);
    hmac.update(payloadB64);
    const expectedSig = hmac.digest("hex");

    // Timing-safe comparison
    const sigBuf = Buffer.from(sig, "hex");
    const expectedBuf = Buffer.from(expectedSig, "hex");
    if (sigBuf.length !== expectedBuf.length || !crypto.timingSafeEqual(sigBuf, expectedBuf)) {
      throw new LicenseError("Cryptographic signature verification failed: invalid or tampered license.");
    }

    // Decode payload
    let claims: LicenseClaims;
    try {
      const rawJson = Buffer.from(payloadB64, "base64url").toString("utf-8");
      claims = JSON.parse(rawJson);
    } catch (err: any) {
      throw new LicenseError(`Failed to decode license payload: ${err.message}`);
    }

    // Check expiration
    const now = Math.floor(Date.now() / 1000);
    if (claims.exp < now) {
      throw new LicenseError(`License token expired at ${claims.exp}. Current time: ${now}`);
    }

    return claims;
  }
}

/**
 * Authority controller used across CLI, MCP, and TypeScript SDK clients.
 */
export class LicenseAuthority {
  public token?: string;
  public secret: string;
  public tier: NephisTier;
  public tenantId: string;
  public entitlements: TierEntitlements;
  public claims?: LicenseClaims;
  public error?: string;

  constructor(token?: string, secret: string = DEFAULT_LICENSE_SECRET) {
    this.token = token;
    this.secret = secret;

    if (token) {
      try {
        const claims = LicenseToken.verify(token, secret);
        this.claims = claims;
        this.tier = claims.tier;
        this.tenantId = claims.tid;
        this.entitlements = claims.ent;
      } catch (err: any) {
        this.tier = "community";
        this.tenantId = "unlicensed";
        this.entitlements = TIERS.community;
        this.error = err.message;
      }
    } else {
      this.tier = "community";
      this.tenantId = "default";
      this.entitlements = TIERS.community;
    }
  }

  /**
   * Assert that the current license tier permits the specified feature.
   */
  assertFeature(featureName: string): boolean {
    const features = this.entitlements.features || [];
    if (features.includes("*") || features.includes(featureName)) {
      return true;
    }
    throw new LicenseError(
      `Feature '${featureName}' requires an upgraded Nephis license tier (Current: ${this.tier.toUpperCase()}). ` +
        `Please upgrade to PRO or ENTERPRISE at https://nephis.theeducode.com/pricing`
    );
  }

  /**
   * Check if a feature is permitted without throwing an error.
   */
  isFeatureAllowed(featureName: string): boolean {
    const features = this.entitlements.features || [];
    return features.includes("*") || features.includes(featureName);
  }

  /**
   * Return structured license status summary.
   */
  status(): LicenseStatus {
    return {
      tier: this.tier,
      tenant_id: this.tenantId,
      is_valid: Boolean(this.claims && !this.error),
      expires_at: this.claims?.exp ?? null,
    };
  }
}

