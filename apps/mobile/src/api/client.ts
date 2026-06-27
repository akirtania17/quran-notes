import { getClientId } from '../storage/asyncStorage';
import { buildApiUrl, getDefaultApiBaseUrl } from '../constants/api';
import { useSettingsStore } from '../state/settingsStore';

export type ApiError = {
  message: string;
  status?: number;
  details?: any;
};

export class ApiClient {
  private clientId: string | null = null;

  private static readonly DEFAULT_TIMEOUT_MS = 15_000;
  private static readonly DEFAULT_MULTIPART_TIMEOUT_MS = 5 * 60_000; // 5 minutes
  
  async ensureClientId(): Promise<string> {
    if (!this.clientId) {
      this.clientId = await getClientId();
    }
    return this.clientId;
  }

  private getBaseUrl(): string {
    const override = useSettingsStore.getState().apiBaseUrl;
    // Compute default dynamically so it can pick up the correct dev host in Expo Go.
    return override || getDefaultApiBaseUrl();
  }

  private getOverrideBaseUrl(): string | null {
    return useSettingsStore.getState().apiBaseUrl;
  }

  private async maybeAutoRecoverBadOverrideOnGet(error: ApiError): Promise<boolean> {
    // Only auto-recover on network-ish failures (no HTTP status).
    // This avoids retrying legitimate 4xx/5xx responses and avoids duplicating non-idempotent requests.
    if (typeof error?.status === 'number') return false;

    const override = this.getOverrideBaseUrl();
    if (!override) return false;

    const msg = (error?.message || '').toLowerCase();
    const isNetworkish =
      msg.includes('network request failed') ||
      msg.includes('timed out') ||
      msg.includes('timeout') ||
      msg.includes('check your api base url');

    if (!isNetworkish) return false;

    try {
      // Clear the override so subsequent requests use the default host.
      await useSettingsStore.getState().resetApiBaseUrl();
      return true;
    } catch {
      return false;
    }
  }

  private async getWithBaseUrl<T>(baseUrl: string, path: string, timeoutMs: number): Promise<T> {
    const clientId = await this.ensureClientId();
    const response = await this.fetchWithTimeout(
      buildApiUrl(baseUrl, path),
      {
        method: 'GET',
        headers: {
          'X-Client-Id': clientId,
        },
      },
      timeoutMs
    );

    if (!response.ok) {
      throw await this.parseError(response);
    }

    return response.json();
  }

  private async parseError(response: Response): Promise<ApiError> {
    const status = response.status;
    const contentType = response.headers.get('content-type') || '';

    let rawText = '';
    try {
      rawText = await response.text();
    } catch {
      // ignore
    }

    // Try JSON first (FastAPI often returns {"detail": "..."})
    if (contentType.includes('application/json')) {
      try {
        const data = rawText ? JSON.parse(rawText) : null;
        const message =
          typeof data?.detail === 'string'
            ? data.detail
            : typeof data?.error === 'string'
              ? data.error
            : typeof data?.message === 'string'
              ? data.message
              : rawText || `Request failed (${status})`;
        return { message, status, details: data };
      } catch {
        // fall through to text
      }
    }

    return { message: rawText || `Request failed (${status})`, status };
  }

  private normalizeThrownError(error: any): ApiError {
    // Timeout/abort
    const name = typeof error?.name === 'string' ? error.name : '';
    const messageStr = typeof error?.message === 'string' ? error.message : '';
    if (name === 'AbortError' || /aborted/i.test(messageStr)) {
      return { message: 'Request timed out. Check your API Base URL and connection.' };
    }
    if (error && typeof error === 'object' && typeof error.message === 'string') {
      return error as ApiError;
    }
    const message =
      typeof error === 'string'
        ? error
        : 'Network request failed. Check your API Base URL and connection.';
    return { message };
  }

  private async fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { ...init, signal: controller.signal });
    } finally {
      clearTimeout(timeoutId);
    }
  }
  
  async get<T>(path: string, timeoutMs: number = ApiClient.DEFAULT_TIMEOUT_MS): Promise<T> {
    try {
      const override = this.getOverrideBaseUrl();
      const baseUrl = this.getBaseUrl();
      // First attempt: use current effective URL (override if set).
      return await this.getWithBaseUrl<T>(baseUrl, path, timeoutMs);
    } catch (error: any) {
      const normalized = this.normalizeThrownError(error);

      // Auto-recover from stale/dev IP overrides for GETs only.
      const didReset = await this.maybeAutoRecoverBadOverrideOnGet(normalized);
      if (didReset) {
        try {
          // Second attempt: with override cleared, base URL will be auto-detected.
          const fallbackBaseUrl = getDefaultApiBaseUrl();
          return await this.getWithBaseUrl<T>(fallbackBaseUrl, path, timeoutMs);
        } catch (e2: any) {
          throw this.normalizeThrownError(e2);
        }
      }

      throw normalized;
    }
  }
  
  async post<T>(path: string, body: any, timeoutMs: number = ApiClient.DEFAULT_TIMEOUT_MS): Promise<T> {
    const clientId = await this.ensureClientId();
    try {
      const response = await this.fetchWithTimeout(buildApiUrl(this.getBaseUrl(), path), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Id': clientId,
        },
        body: JSON.stringify(body),
      }, timeoutMs);

      if (!response.ok) {
        throw await this.parseError(response);
      }

      return response.json();
    } catch (error: any) {
      throw this.normalizeThrownError(error);
    }
  }

  async patch<T>(path: string, body: any, timeoutMs: number = ApiClient.DEFAULT_TIMEOUT_MS): Promise<T> {
    const clientId = await this.ensureClientId();
    try {
      const response = await this.fetchWithTimeout(buildApiUrl(this.getBaseUrl(), path), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Id': clientId,
        },
        body: JSON.stringify(body),
      }, timeoutMs);

      if (!response.ok) {
        throw await this.parseError(response);
      }

      return response.json();
    } catch (error: any) {
      throw this.normalizeThrownError(error);
    }
  }

  async delete<T>(path: string, timeoutMs: number = ApiClient.DEFAULT_TIMEOUT_MS): Promise<T> {
    const clientId = await this.ensureClientId();
    try {
      const response = await this.fetchWithTimeout(buildApiUrl(this.getBaseUrl(), path), {
        method: 'DELETE',
        headers: {
          'X-Client-Id': clientId,
        },
      }, timeoutMs);

      if (!response.ok) {
        throw await this.parseError(response);
      }

      // Some DELETE endpoints may return empty bodies; tolerate that.
      const text = await response.text();
      return (text ? JSON.parse(text) : ({} as any)) as T;
    } catch (error: any) {
      throw this.normalizeThrownError(error);
    }
  }
  
  async postMultipart<T>(
    path: string,
    formData: FormData,
    timeoutMs: number = ApiClient.DEFAULT_MULTIPART_TIMEOUT_MS
  ): Promise<T> {
    const clientId = await this.ensureClientId();
    try {
      const response = await this.fetchWithTimeout(buildApiUrl(this.getBaseUrl(), path), {
        method: 'POST',
        headers: {
          'X-Client-Id': clientId,
        },
        body: formData,
      }, timeoutMs);

      if (!response.ok) {
        throw await this.parseError(response);
      }

      return response.json();
    } catch (error: any) {
      throw this.normalizeThrownError(error);
    }
  }
}

export const apiClient = new ApiClient();

