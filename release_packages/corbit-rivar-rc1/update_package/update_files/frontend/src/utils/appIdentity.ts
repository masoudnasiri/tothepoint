/* eslint-disable @typescript-eslint/no-explicit-any */
declare const process: any;

export const PRODUCT_NAME = 'Rivar';
export const PRODUCER_NAME = 'Corbit';
export const BRAND_NAME = `${PRODUCT_NAME} by ${PRODUCER_NAME}`;

const rawApiBaseUrl = process.env.REACT_APP_API_URL || '';
const normalizedApiBaseUrl = rawApiBaseUrl.replace('://localhost:', '://127.0.0.1:');
const healthUrl = normalizedApiBaseUrl ? `${normalizedApiBaseUrl}/health` : '/health';

export async function getRuntimeVersion(): Promise<string> {
  try {
    const response = await fetch(healthUrl);
    if (!response.ok) {
      return 'unknown';
    }

    const payload = await response.json();
    if (typeof payload?.version === 'string' && payload.version.trim().length > 0) {
      return payload.version;
    }

    return 'unknown';
  } catch {
    return 'unknown';
  }
}
