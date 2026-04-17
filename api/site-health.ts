/**
 * Vercel serverless function – site health diagnostics.
 *
 * POST /api/site-health
 * Body: { url: string, timeout?: number }
 * Returns JSON with site health result.
 */

const URL_PATTERN = /^https?:\/\/.+/i;

export default function handler(req: any, res: any) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body ?? {};
    const url: string = typeof body.url === "string" ? body.url.trim() : "";

    if (!url) {
      return res.status(422).json({ error: "url is required" });
    }

    if (!URL_PATTERN.test(url)) {
      return res.status(422).json({ error: "url must be a valid HTTP/HTTPS URL" });
    }

    const timeout = typeof body.timeout === "number" ? body.timeout : 10;
    if (timeout < 1 || timeout > 60) {
      return res.status(422).json({ error: "timeout must be between 1 and 60" });
    }

    let hostname: string;
    try {
      hostname = new URL(url).hostname;
    } catch {
      return res.status(422).json({ error: "url is not a valid URL" });
    }

    return res.status(501).json({
      error: "Site health diagnostics are not yet implemented in this runtime",
      hostname,
    });
  } catch (err) {
    console.error("[site-health] Unhandled error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
