import { Note } from '../types/contracts';
import { apiClient } from './client';

export type NotesListResponse = {
  items: Note[];
};

export type CreateNoteRequest = {
  sessionId: string;
  text: string;
};

export async function createNote(request: CreateNoteRequest): Promise<Note> {
  const response = await apiClient.post<any>(
    `/v1/sessions/${request.sessionId}/notes`,
    { text: request.text }
  );
  return mapNoteFromApi(response);
}

export async function listNotes(sessionId: string): Promise<Note[]> {
  const response = await apiClient.get<any>(`/v1/sessions/${sessionId}/notes`);
  return response.items.map(mapNoteFromApi);
}

// Map snake_case API response to camelCase
function mapNoteFromApi(data: any): Note {
  return {
    id: data.id,
    sessionId: data.session_id,
    text: data.text,
    createdAt: data.created_at,
  };
}

