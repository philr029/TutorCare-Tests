import type { PhoneCheckResult } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export interface PhoneCheckResponse {
  success: true;
  input: string;
  provider: PhoneCheckResult;
}

export interface ApiErrorResponse {
  success: false;
  error: string;
}

export type NumverifyApiResponse = PhoneCheckResponse | ApiErrorResponse;

/**
 * Calls the /api/numverify serverless function and returns a typed result.
 * Returns an error shape on network failure or unexpected response shape.
 */
export async function checkPhone(phone: string): Promise<NumverifyApiResponse> {
  const trimmed = phone.trim();
  if (!trimmed) {
    return { success: false, error: 'Please enter a phone number.' };
  }

  const url = `${API_BASE}/numverify`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: trimmed }),
    });
  } catch {
    return { success: false, error: 'Network error – could not reach the API.' };
  }

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    return { success: false, error: `Server returned an unparseable response (HTTP ${res.status}).` };
  }

  if (
    body !== null &&
    typeof body === 'object' &&
    'success' in body
  ) {
    return body as NumverifyApiResponse;
  }

  return { success: false, error: 'Unexpected response format from server.' };
}
