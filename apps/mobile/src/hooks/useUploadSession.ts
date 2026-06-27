import { useState } from 'react';
import { createSession, CreateSessionRequest } from '../api/sessions';
import { apiClient } from '../api/client';
import { Session } from '../types/contracts';
import { useSessionsStore } from '../state/sessionsStore';
import { useStatsStore } from '../state/statsStore';
import * as FileSystem from 'expo-file-system';
import { MAX_UPLOAD_BYTES, MAX_UPLOAD_MB } from '../constants/uploads';

type UploadState = {
  isUploading: boolean;
  error: string | null;
  progress: number;
};

export function useUploadSession() {
  const [state, setState] = useState<UploadState>({
    isUploading: false,
    error: null,
    progress: 0,
  });
  
  const addSession = useSessionsStore((s) => s.addSession);
  const awardUploadXP = useStatsStore((s) => s.awardUploadXP);

  function isRetryable(error: any): boolean {
    // ApiError produced by ApiClient may include status.
    const status = typeof error?.status === 'number' ? error.status : undefined;
    if (status == null) return true; // network / unknown
    if (status === 408) return true;
    if (status === 429) return true;
    return status >= 500;
  }

  async function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
  
  async function upload(request: CreateSessionRequest): Promise<Session | null> {
    setState({ isUploading: true, error: null, progress: 0 });
    
    try {
      // Fast-fail if backend is unreachable (prevents infinite spinner on device).
      try {
        await apiClient.get('/v1/health', 6000);
      } catch {
        setState({
          isUploading: false,
          error:
            "Can't reach the backend. Make sure it’s running and set Settings → API Base URL to your computer IP (e.g. http://192.168.x.x:8000).",
          progress: 0,
        });
        return null;
      }

      // Preflight: check file size (helps fail fast for long recordings)
      try {
        const info = await FileSystem.getInfoAsync(request.audioUri);
        const size = (info as any)?.size as number | undefined;
        if (typeof size === 'number' && size > MAX_UPLOAD_BYTES) {
          setState({
            isUploading: false,
            error: `Audio file too large. Max is ${MAX_UPLOAD_MB} MB.`,
            progress: 0,
          });
          return null;
        }
      } catch {
        // If we can't read file info, continue and let the server validate.
      }

      // Simulate progress (FormData upload doesn't provide real progress easily)
      setState((s) => ({ ...s, progress: 30 }));
      
      const maxAttempts = 2; // 1 retry
      let lastError: any = null;
      let session: Session | null = null;
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          session = await createSession(request);
          break;
        } catch (error: any) {
          lastError = error;
          if (attempt === maxAttempts - 1 || !isRetryable(error)) {
            throw error;
          }
          // Backoff (w/ jitter). Use longer delay for 429.
          const jitter = Math.floor(Math.random() * 300);
          const status = typeof error?.status === 'number' ? error.status : undefined;
          const baseMs =
            status === 429
              ? attempt === 0
                ? 3000
                : 6000
              : attempt === 0
                ? 1000
                : 3000;
          const delayMs = baseMs + jitter;
          setState((s) => ({ ...s, progress: 30, error: `Upload failed, retrying… (${attempt + 1}/${maxAttempts})` }));
          await sleep(delayMs);
        }
      }
      if (!session) {
        throw lastError || new Error('Failed to upload session');
      }
      
      setState((s) => ({ ...s, progress: 100 }));
      
      // Add to store
      addSession(session);
      
      // Award XP
      await awardUploadXP(session.id);
      
      setState({ isUploading: false, error: null, progress: 100 });
      return session;
    } catch (error: any) {
      const message = error.message || 'Failed to upload session';
      setState({ isUploading: false, error: message, progress: 0 });
      return null;
    }
  }
  
  function reset(): void {
    setState({ isUploading: false, error: null, progress: 0 });
  }
  
  return {
    ...state,
    upload,
    reset,
  };
}

