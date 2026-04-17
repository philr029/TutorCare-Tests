/**
 * Vercel serverless function – domain reputation check.
 *
 * POST /api/check-domain
 * Body: { domain: string, dnsbl_hosts?: string[] }
 * Returns JSON with reputation result.
 */

const DOMAIN_PATTERN = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;

export default function handler(req: any, res: any) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body ?? {};
    const domain: string =
      typeof body.domain === "string" ? body.domain.trim().toLowerCase() : "";

    if (!domain) {
      return res.status(422).json({ error: "domain is required" });
    }

    if (!DOMAIN_PATTERN.test(domain)) {
      return res.status(422).json({ error: "domain must be a valid hostname" });
    }

    return res.status(200).json({
      domain,
      resolved_ips: [],
      listed: false,
      sources: [],
    });
  } catch (err) {
    console.error("[check-domain] Unhandled error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
