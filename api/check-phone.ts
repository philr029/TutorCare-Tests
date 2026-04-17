/**
 * Vercel serverless function – phone number validation.
 *
 * POST /api/check-phone
 * Body: { phone: string, region?: string }
 * Returns JSON with validation result.
 */

const E164_PATTERN = /^\+[1-9]\d{1,14}$/;

export default function handler(req: any, res: any) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const body = req.body ?? {};
    const phone: string = typeof body.phone === "string" ? body.phone.trim() : "";

    if (!phone) {
      return res.status(422).json({ error: "phone must not be empty" });
    }

    const valid = E164_PATTERN.test(phone);

    return res.status(200).json({
      input: phone,
      valid,
      possible: valid,
      format: valid
        ? {
            e164: phone,
            international: phone,
            national: phone.replace(/^\+\d+\s?/, ""),
          }
        : null,
      country: null,
      region: body.region ?? null,
      carrier: null,
      line_type: null,
      timezones: [],
      sources: [],
      error: valid ? null : "Phone number does not match E.164 format",
    });
  } catch (err) {
    console.error("[check-phone] Unhandled error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
