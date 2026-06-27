import { NativeModules, Platform } from 'react-native';
import Constants from 'expo-constants';

// Default API base URL for the mobile app.
//
// Notes:
// - On a physical device (Expo Go), `localhost` points to the phone, not your computer.
// - In dev, we can auto-detect the dev machine host from the Metro bundle URL.
// - You can still override at runtime via Settings (preferred) or via Expo env var.
function isPrivateIPv4(host: string): boolean {
  // Very small, dependency-free check for RFC1918 ranges.
  // - 10.0.0.0/8
  // - 172.16.0.0/12
  // - 192.168.0.0/16
  const m = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!m) return false;
  const a = Number(m[1]);
  const b = Number(m[2]);
  const c = Number(m[3]);
  const d = Number(m[4]);
  if ([a, b, c, d].some((n) => !Number.isFinite(n) || n < 0 || n > 255)) return false;
  if (a === 10) return true;
  if (a === 192 && b === 168) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  return false;
}

function isLikelyDevHost(host: string): boolean {
  const h = host.toLowerCase();
  if (h === 'localhost' || h === '127.0.0.1') return true; // simulators / web
  if (h === '10.0.2.2') return true; // Android emulator
  if (isPrivateIPv4(h)) return true; // LAN IP (physical devices)
  return false;
}

function getDevHostFromExpoConstants(): string | null {
  // Common places across SDKs:
  // - Constants.expoConfig.hostUri: "192.168.x.x:8081"
  // - Constants.manifest.debuggerHost: "192.168.x.x:8081"
  // - Constants.manifest2.extra.expoClient.hostUri: "192.168.x.x:8081"
  const hostUri =
    (Constants as any)?.expoConfig?.hostUri ??
    (Constants as any)?.manifest?.debuggerHost ??
    (Constants as any)?.manifest2?.extra?.expoClient?.hostUri ??
    null;

  if (!hostUri || typeof hostUri !== 'string') return null;

  // hostUri is typically "<host>:<port>"
  const host = hostUri.split(':')[0];
  if (!host) return null;
  return isLikelyDevHost(host) ? host : null;
}

function getDevHostFromMetroScriptURL(): string | null {
  const scriptURL = (NativeModules as any)?.SourceCode?.scriptURL as string | undefined;
  if (!scriptURL || typeof scriptURL !== 'string') return null;

  // Typical dev URLs:
  // - http://192.168.x.x:8081/index.bundle?platform=ios&dev=true...
  // - http://10.0.2.2:8081/index.bundle?platform=android&dev=true...
  // - exp://192.168.x.x:8081 (Expo Go)
  // - exps://192.168.x.x:8081 (Expo Go secure)
  const match = scriptURL.match(/^(?:https?|exp|exps):\/\/([^:/]+)(?::\d+)?/i);
  const host = match?.[1] ?? null;
  if (!host) return null;
  return isLikelyDevHost(host) ? host : null;
}

export function getDefaultApiBaseUrl(): string {
  const env = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (env) return env;

  // Web dev is usually running on the same machine.
  if (Platform.OS === 'web') return 'http://localhost:8000';

  const host = getDevHostFromExpoConstants() || getDevHostFromMetroScriptURL();
  if (host) return `http://${host}:8000`;

  // Fallback:
  // - iOS simulator often works with localhost
  // - physical devices must override in Settings OR ensure Expo is using LAN (not Tunnel)
  if ((Constants as any)?.isDevice) {
    // On a real phone, localhost points to the phone itself, so this will not work.
    // Keep it as a last resort, but the upload preflight will surface a clear error.
    return 'http://localhost:8000';
  }
  return 'http://localhost:8000';
}

export const DEFAULT_API_BASE_URL = getDefaultApiBaseUrl();

export const APP_ENV = process.env.EXPO_PUBLIC_APP_ENV || (__DEV__ ? 'dev' : 'prod');

export function normalizeApiBaseUrl(input: string): string | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  // Remove trailing slashes to avoid `//v1/...` when concatenating.
  const noTrailingSlash = trimmed.replace(/\/+$/, '');

  // If the user enters "192.168.1.10:8000", assume http://
  if (!/^https?:\/\//i.test(noTrailingSlash)) {
    return `http://${noTrailingSlash}`;
  }

  return noTrailingSlash;
}

export function buildApiUrl(baseUrl: string, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return new URL(normalizedPath, baseUrl).toString();
}


