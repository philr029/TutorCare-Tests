/**
 * Vercel serverless function – health check.
 *
 * GET /api/health
 * Returns JSON: { status: "ok", service: "security-toolkit-api" }
 */
export default function handler(req: any, res: any) {
  try {
    res.status(200).json({
      status: "ok",
      service: "security-toolkit-api",
      abuseipdb_loaded: Boolean(process.env.ABUSEIPDB_KEY),
      virustotal_loaded: Boolean(process.env.VIRUSTOTAL_KEY),
      numverify_loaded: Boolean(process.env.NUMVERIFY_API_KEY),
      twilio_loaded: Boolean(process.env.TWILIO_SID && process.env.TWILIO_TOKEN),
    });
  } catch (err) {
    console.error("[health] Unhandled error:", err);
    res.status(500).json({ status: "error", error: "Internal server error" });
  }
}
