import { Language } from '../types/contracts';

// Default languages list (will be fetched from API but this is fallback)
export const DEFAULT_LANGUAGES: Language[] = [
  { code: 'en', label: 'English' },
  { code: 'ar', label: 'Arabic' },
  { code: 'fr', label: 'French' },
  { code: 'ur', label: 'Urdu' },
  { code: 'tr', label: 'Turkish' },
  { code: 'id', label: 'Indonesian' },
];

export const DEFAULT_TARGET_LANGUAGE = 'en';

