import { create } from 'zustand';
import { Highlight, Session } from '../types/contracts';
import { setBookmarked as apiSetBookmarked } from '../api/sessions';
import { createHighlight, deleteHighlight, listHighlights } from '../api/highlights';

type SessionsState = {
  sessions: Session[];
  sessionsMap: Record<string, Session>;
  highlightsBySessionId: Record<string, Highlight[]>;
  isLoading: boolean;
  error: string | null;
  nextOffset: number | null;
  
  // Actions
  setSessions: (sessions: Session[], nextOffset: number | null) => void;
  addSession: (session: Session) => void;
  updateSession: (session: Session) => void;
  getSession: (id: string) => Session | undefined;
  setBookmarked: (sessionId: string, bookmarked: boolean) => Promise<void>;
  fetchHighlights: (sessionId: string) => Promise<void>;
  addHighlight: (sessionId: string, text: string) => Promise<Highlight>;
  removeHighlight: (sessionId: string, highlightId: string) => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearSessions: () => void;
};

export const useSessionsStore = create<SessionsState>((set, get) => ({
  sessions: [],
  sessionsMap: {},
  highlightsBySessionId: {},
  isLoading: false,
  error: null,
  nextOffset: null,
  
  setSessions: (sessions: Session[], nextOffset: number | null) => {
    const map: Record<string, Session> = {};
    sessions.forEach((s) => {
      map[s.id] = s;
    });
    set({
      sessions,
      sessionsMap: { ...get().sessionsMap, ...map },
      nextOffset,
      isLoading: false,
    });
  },
  
  addSession: (session: Session) => {
    set({
      sessions: [session, ...get().sessions],
      sessionsMap: { ...get().sessionsMap, [session.id]: session },
    });
  },
  
  updateSession: (session: Session) => {
    const sessions = get().sessions.map((s) => (s.id === session.id ? session : s));
    set({
      sessions,
      sessionsMap: { ...get().sessionsMap, [session.id]: session },
    });
  },
  
  getSession: (id: string) => {
    return get().sessionsMap[id];
  },

  setBookmarked: async (sessionId: string, bookmarked: boolean) => {
    const prev = get().sessionsMap[sessionId];
    if (!prev) return;

    // optimistic update
    const optimistic: Session = { ...prev, bookmarked };
    get().updateSession(optimistic);

    try {
      const updated = await apiSetBookmarked(sessionId, bookmarked);
      get().updateSession(updated);
    } catch (e) {
      // revert
      get().updateSession(prev);
      throw e;
    }
  },

  fetchHighlights: async (sessionId: string) => {
    const items = await listHighlights(sessionId);
    set({
      highlightsBySessionId: { ...get().highlightsBySessionId, [sessionId]: items },
    });
  },

  addHighlight: async (sessionId: string, text: string) => {
    const created = await createHighlight({ sessionId, text });
    const existing = get().highlightsBySessionId[sessionId] || [];
    set({
      highlightsBySessionId: {
        ...get().highlightsBySessionId,
        [sessionId]: [created, ...existing],
      },
    });
    return created;
  },

  removeHighlight: async (sessionId: string, highlightId: string) => {
    // optimistic remove
    const existing = get().highlightsBySessionId[sessionId] || [];
    const next = existing.filter((h) => h.id !== highlightId);
    set({
      highlightsBySessionId: { ...get().highlightsBySessionId, [sessionId]: next },
    });

    try {
      await deleteHighlight(sessionId, highlightId);
    } catch (e) {
      // revert on failure
      set({
        highlightsBySessionId: { ...get().highlightsBySessionId, [sessionId]: existing },
      });
      throw e;
    }
  },
  
  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },
  
  setError: (error: string | null) => {
    set({ error, isLoading: false });
  },
  
  clearSessions: () => {
    set({
      sessions: [],
      sessionsMap: {},
      highlightsBySessionId: {},
      isLoading: false,
      error: null,
      nextOffset: null,
    });
  },
}));

