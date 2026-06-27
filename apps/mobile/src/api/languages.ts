import { Language } from '../types/contracts';
import { apiClient } from './client';

export type LanguagesResponse = {
  items: Language[];
};

export async function listLanguages(): Promise<Language[]> {
  const response = await apiClient.get<LanguagesResponse>('/v1/languages');
  return response.items;
}

