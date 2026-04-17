/**
 * Vercel serverless function – IP reputation check.
 *
 * POST /api/check-ip
 * Body: { ip: string, dnsbl_zones?: string[] }
 * Returns JSON with reputation result.
 */

const IPV4_PATTERN = /^(\d{1,3}\.){3}\d{1,3}$/;

function isValidIPv4(ip: string): boolean {
  if (!IPV4_PATTERN.test(ip)) return false;
  return ip.split(".").every((octet) => {
    const n = parseInt(octet, 10);
    return n >= 0 && n <= 255;
  });
}

export default function handler(req: any, res: any) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body ?? {};
    const ip: string = typeof body.ip === "string" ? body.ip.trim() : "";

    if (!ip) {
      return res.status(422).json({ error: "ip is required" });
    }

    if (!isValidIPv4(ip)) {
      return res.status(422).json({ error: "ip must be a valid IPv4 address" });
    }

    return res.status(200).json({
      ip,
      dnsbl_results: [],
      abuseipdb: null,
    });
  } catch (err) {
    console.error("[check-ip] Unhandled error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
