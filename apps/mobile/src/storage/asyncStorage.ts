import AsyncStorage from '@react-native-async-storage/async-storage';
import { Stats } from '../types/contracts';

const KEYS = {
  CLIENT_ID: 'client_id_v1',
  STATS: 'stats_v1',
  DEFAULT_LANGUAGE: 'default_language_v1',
  API_BASE_URL: 'api_base_url_v1',
};

// Client ID (anonymous device token)
export async function getClientId(): Promise<string> {
  const existing = await AsyncStorage.getItem(KEYS.CLIENT_ID);
  if (existing) return existing;
  
  const newId = generateUUID();
  await AsyncStorage.setItem(KEYS.CLIENT_ID, newId);
  return newId;
}

export async function resetClientId(): Promise<void> {
  await AsyncStorage.removeItem(KEYS.CLIENT_ID);
}

// Stats (XP + streak)
export async function getStats(): Promise<Stats> {
  const json = await AsyncStorage.getItem(KEYS.STATS);
  if (!json) {
    return {
      xp: 0,
      streakCount: 0,
      lastStreakDate: null,
      openedCompleteSessionIds: [],
      uploadedSessionIds: [],
    };
  }
  const parsed = JSON.parse(json) as Stats;
  return {
    uploadedSessionIds: parsed.uploadedSessionIds || [],
    ...parsed,
  };
}

export async function saveStats(stats: Stats): Promise<void> {
  await AsyncStorage.setItem(KEYS.STATS, JSON.stringify(stats));
}

// Default language setting
export async function getDefaultLanguage(): Promise<string> {
  return (await AsyncStorage.getItem(KEYS.DEFAULT_LANGUAGE)) || 'en';
}

export async function saveDefaultLanguage(code: string): Promise<void> {
  await AsyncStorage.setItem(KEYS.DEFAULT_LANGUAGE, code);
}

// API base URL setting (null = use app default)
export async function getApiBaseUrl(): Promise<string | null> {
  return (await AsyncStorage.getItem(KEYS.API_BASE_URL)) || null;
}

export async function saveApiBaseUrl(url: string | null): Promise<void> {
  if (!url) {
    await AsyncStorage.removeItem(KEYS.API_BASE_URL);
    return;
  }
  await AsyncStorage.setItem(KEYS.API_BASE_URL, url);
}

// Danger-zone clear: wipes local stats/settings overrides (optionally client id)
export async function clearAppData(opts?: { resetClientId?: boolean }): Promise<void> {
  const { resetClientId: shouldResetClientId = false } = opts || {};
  const removals = [
    AsyncStorage.removeItem(KEYS.STATS),
    AsyncStorage.removeItem(KEYS.DEFAULT_LANGUAGE),
    AsyncStorage.removeItem(KEYS.API_BASE_URL),
  ];
  if (shouldResetClientId) {
    removals.push(AsyncStorage.removeItem(KEYS.CLIENT_ID));
  }
  await Promise.all(removals);
}

// Simple UUID generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

