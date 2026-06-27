import { Highlight } from '../types/contracts';
import { apiClient } from './client';

export type CreateHighlightRequest = {
  sessionId: string;
  text: string;
};

export async function createHighlight(request: CreateHighlightRequest): Promise<Highlight> {
  const response = await apiClient.post<any>(
    `/v1/sessions/${request.sessionId}/highlights`,
    { text: request.text }
  );
  return mapHighlightFromApi(response);
}

export async function listHighlights(sessionId: string): Promise<Highlight[]> {
  const response = await apiClient.get<any>(`/v1/sessions/${sessionId}/highlights`);
  // backend returns a plain list
  return (response as any[]).map(mapHighlightFromApi);
}

export async function deleteHighlight(sessionId: string, highlightId: string): Promise<void> {
  await apiClient.delete(`/v1/sessions/${sessionId}/highlights/${highlightId}`);
}

function mapHighlightFromApi(data: any): Highlight {
  return {
    id: data.id,
    sessionId: data.session_id,
    text: data.text,
    createdAt: data.created_at,
  };
}


