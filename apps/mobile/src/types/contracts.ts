// Data contracts matching backend API
export type SessionStatus = 'uploaded' | 'processing' | 'complete' | 'failed';

export type Session = {
  id: string;
  clientId: string;
  title: string;
  createdAt: string; // ISO timestamp
  durationSeconds: number | null;
  audioPath: string;
  status: SessionStatus;
  processingStep: string | null;
  progressPct: number | null;
  sourceLanguage: string | null;
  targetLanguage: string;
  transcript: string | null;
  translation: string | null;
  summaryBullets: string[] | null;
  errorMessage: string | null;
  bookmarked: boolean;

  // Automatic Ayah linking (Arabic-only MVP)
  matchedSurah?: number | null;
  matchedAyah?: number | null;
  matchedAyahTextAr?: string | null;
  matchedConfidencePct?: number | null;
  matchedMethod?: string | null;
  matchedCandidates?: Array<{
    surah: number;
    ayah: number;
    scorePct: number;
    textAr: string;
  }> | null;
};

export type Note = {
  id: string;
  sessionId: string;
  text: string;
  createdAt: string; // ISO timestamp
};

export type Highlight = {
  id: string;
  sessionId: string;
  text: string;
  createdAt: string; // ISO timestamp
};

export type Stats = {
  xp: number;
  streakCount: number;
  lastStreakDate: string | null; // YYYY-MM-DD
  openedCompleteSessionIds: string[]; // capped list to avoid repeated +2 abuse
  uploadedSessionIds?: string[]; // optional legacy field, dedupe uploads
};

export type Language = {
  code: string;
  label: string;
};

