/**
 * Vercel serverless function – NumVerify phone validation proxy.
 *
 * Accepts GET or POST requests with a `phone` parameter and returns the
 * NumVerify API response wrapped in a standard envelope:
 *
 *   { success: true,  input: "<phone>", provider: { ...numverify payload... } }
 *   { success: false, error: "<message>" }
 *
 * Required environment variable:
 *   NUMVERIFY_API_KEY  – NumVerify access key (apilayer.net)
 */

const NUMVERIFY_BASE_URL = "http://apilayer.net/api/validate";

module.exports = async function handler(req, res) {
  try {
    const apiKey = process.env.NUMVERIFY_API_KEY;
    if (!apiKey) {
      return res
        .status(200)
        .json({ success: false, error: "Missing NUMVERIFY_API_KEY" });
    }

    const phone =
      req.method === "POST"
        ? req.body && req.body.phone
        : req.query && req.query.phone;

    if (!phone) {
      return res
        .status(400)
        .json({ success: false, error: "Missing phone number" });
    }

    const url = new URL(NUMVERIFY_BASE_URL);
    url.searchParams.set("access_key", apiKey);
    url.searchParams.set("number", String(phone));
    url.searchParams.set("format", "1");

    let upstreamResponse;
    try {
      upstreamResponse = await fetch(url.toString());
    } catch (fetchError) {
      console.error("[numverify] Upstream fetch failed:", fetchError);
      return res
        .status(502)
        .json({ success: false, error: "Failed to reach NumVerify API" });
    }

    let data;
    try {
      data = await upstreamResponse.json();
    } catch (parseError) {
      console.error("[numverify] Failed to parse NumVerify response:", parseError);
      return res
        .status(502)
        .json({ success: false, error: "Invalid response from NumVerify" });
    }

    return res.status(200).json({
      success: true,
      input: String(phone),
      provider: data,
    });
  } catch (err) {
    console.error("[numverify] Unhandled error:", err);
    return res
      .status(500)
      .json({ success: false, error: "Internal server error" });
  }
};
