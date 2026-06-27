import { Session } from '../types/contracts';
import { apiClient } from './client';

export type SessionsListResponse = {
  items: Session[];
  next_offset: number | null;
};

export type CreateSessionRequest = {
  title: string;
  targetLanguage: string;
  durationSeconds?: number;
  audioUri: string;
};

export async function createSession(request: CreateSessionRequest): Promise<Session> {
  const formData = new FormData();
  formData.append('title', request.title);
  formData.append('target_language', request.targetLanguage);
  
  if (request.durationSeconds != null) {
    formData.append('duration_seconds', String(request.durationSeconds));
  }
  
  // Create file object for audio
  const audioFile = {
    uri: request.audioUri,
    name: 'audio.m4a',
    type: 'audio/mp4',
  } as any;
  
  formData.append('audio', audioFile);
  
  const response = await apiClient.postMultipart<any>('/v1/sessions', formData);
  return mapSessionFromApi(response);
}

export async function listSessions(offset: number = 0, limit: number = 20): Promise<SessionsListResponse> {
  const response = await apiClient.get<any>(`/v1/sessions?offset=${offset}&limit=${limit}`);
  return {
    items: response.items.map(mapSessionFromApi),
    next_offset: response.next_offset,
  };
}

export async function getSession(id: string): Promise<Session> {
  const response = await apiClient.get<any>(`/v1/sessions/${id}`);
  return mapSessionFromApi(response);
}

export async function retrySession(id: string): Promise<void> {
  await apiClient.post(`/v1/sessions/${id}/retry`, {});
}

export async function setBookmarked(id: string, bookmarked: boolean): Promise<Session> {
  // Use POST for broad compatibility (some backends/proxies/mobile stacks can be finicky with PATCH).
  // Backend implements both PATCH /v1/sessions/{id} and POST /v1/sessions/{id}/bookmark.
  const response = await apiClient.post<any>(`/v1/sessions/${id}/bookmark`, { bookmarked });
  return mapSessionFromApi(response);
}

// Map snake_case API response to camelCase
function mapSessionFromApi(data: any): Session {
  return {
    id: data.id,
    clientId: data.client_id,
    title: data.title,
    createdAt: data.created_at,
    durationSeconds: data.duration_seconds,
    audioPath: data.audio_path,
    status: data.status,
    processingStep: data.processing_step ?? null,
    progressPct: data.progress_pct ?? null,
    sourceLanguage: data.source_language,
    targetLanguage: data.target_language,
    transcript: data.transcript,
    translation: data.translation,
    summaryBullets: data.summary_bullets,
    errorMessage: data.error_message,
    bookmarked: Boolean(data.bookmarked),

    matchedSurah: data.matched_surah ?? null,
    matchedAyah: data.matched_ayah ?? null,
    matchedAyahTextAr: data.matched_ayah_text_ar ?? null,
    matchedConfidencePct: data.matched_confidence_pct ?? null,
    matchedMethod: data.matched_method ?? null,
    matchedCandidates: Array.isArray(data.matched_candidates)
      ? data.matched_candidates.map((c: any) => ({
          surah: c.surah,
          ayah: c.ayah,
          scorePct: c.score_pct,
          textAr: c.text_ar,
        }))
      : null,
  };
}

