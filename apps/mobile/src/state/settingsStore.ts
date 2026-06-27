import { create } from 'zustand';
import { Language } from '../types/contracts';
import { DEFAULT_LANGUAGES, DEFAULT_TARGET_LANGUAGE } from '../constants/languages';
import { getApiBaseUrl, getDefaultLanguage, saveApiBaseUrl, saveDefaultLanguage } from '../storage/asyncStorage';
import { buildApiUrl, normalizeApiBaseUrl } from '../constants/api';

type SettingsState = {
  languages: Language[];
  defaultTargetLanguage: string;
  apiBaseUrl: string | null;
  lastAutoResetApiBaseUrl: string | null;
  isLoaded: boolean;
  
  // Actions
  loadSettings: () => Promise<void>;
  setDefaultLanguage: (code: string) => Promise<void>;
  setApiBaseUrl: (url: string | null) => Promise<void>;
  resetApiBaseUrl: () => Promise<void>;
  setLanguages: (languages: Language[]) => void;
};

async function canReachBackend(baseUrl: string, timeoutMs: number = 2500): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(buildApiUrl(baseUrl, '/v1/health'), {
      method: 'GET',
      signal: controller.signal,
    });
    return resp.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const useSettingsStore = create<SettingsState>((set) => ({
  languages: DEFAULT_LANGUAGES,
  defaultTargetLanguage: DEFAULT_TARGET_LANGUAGE,
  apiBaseUrl: null,
  lastAutoResetApiBaseUrl: null,
  isLoaded: false,
  
  loadSettings: async () => {
    const [defaultLang, storedApiBaseUrl] = await Promise.all([getDefaultLanguage(), getApiBaseUrl()]);

    // Safety: if the stored override points to a dead host (common when LAN IP changes),
    // clear it so the app can still launch and use the dynamic default dev host.
    let apiBaseUrl = storedApiBaseUrl;
    let lastAutoResetApiBaseUrl: string | null = null;

    if (storedApiBaseUrl) {
      const ok = await canReachBackend(storedApiBaseUrl);
      if (!ok) {
        lastAutoResetApiBaseUrl = storedApiBaseUrl;
        apiBaseUrl = null;
        await saveApiBaseUrl(null);
      }
    }

    set({ defaultTargetLanguage: defaultLang, apiBaseUrl, lastAutoResetApiBaseUrl, isLoaded: true });
  },
  
  setDefaultLanguage: async (code: string) => {
    await saveDefaultLanguage(code);
    set({ defaultTargetLanguage: code });
  },

  setApiBaseUrl: async (url: string | null) => {
    const normalized = url == null ? null : normalizeApiBaseUrl(url);
    // Update state first so API calls immediately use the new value.
    set({ apiBaseUrl: normalized, lastAutoResetApiBaseUrl: null });
    await saveApiBaseUrl(normalized);
  },

  resetApiBaseUrl: async () => {
    set({ apiBaseUrl: null, lastAutoResetApiBaseUrl: null });
    await saveApiBaseUrl(null);
  },
  
  setLanguages: (languages: Language[]) => {
    set({ languages });
  },
}));

