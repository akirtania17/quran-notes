import { useState, useEffect, useRef } from 'react';
import { getSession } from '../api/sessions';
import { useSessionsStore } from '../state/sessionsStore';

const POLL_INTERVAL_MS = 2500;
const BACKOFF_START_MS = 120_000; // 2 minutes
const MAX_TIMEOUT_MS = 2_700_000; // 45 minutes
const MAX_INTERVAL_MS = 15_000;

type PollingState = {
  isPolling: boolean;
  error: string | null;
};

export function useSessionPolling(sessionId: string | null, enabled: boolean = true) {
  const [state, setState] = useState<PollingState>({
    isPolling: false,
    error: null,
  });
  const [retryKey, setRetryKey] = useState(0);
  
  const updateSession = useSessionsStore((s) => s.updateSession);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);
  const errorStreakRef = useRef<number>(0);
  
  useEffect(() => {
    if (!sessionId || !enabled) {
      stopPolling();
      return;
    }

    const id = sessionId;
    
    let currentIntervalMs = POLL_INTERVAL_MS;
    startTimeRef.current = Date.now();
    errorStreakRef.current = 0;
    
    async function poll() {
      try {
        const elapsed = Date.now() - startTimeRef.current;
        
        // Timeout check
        if (elapsed > MAX_TIMEOUT_MS) {
          setState({
            isPolling: false,
            error: 'This is taking longer than expected. Pull to refresh or tap Retry.',
          });
          stopPolling();
          return;
        }
        
        const session = await getSession(id);
        updateSession(session);

        // Success: clear transient error state and reset error streak
        if (errorStreakRef.current !== 0) {
          errorStreakRef.current = 0;
        }
        setState((s) => (s.error ? { isPolling: true, error: null } : s));
        
        // Stop if complete or failed
        if (session.status === 'complete' || session.status === 'failed') {
          setState({ isPolling: false, error: null });
          stopPolling();
          return;
        }
        
        // Backoff after 2 minutes
        if (elapsed > BACKOFF_START_MS) {
          currentIntervalMs = Math.min(currentIntervalMs + 500, MAX_INTERVAL_MS);
        }
        
        // Schedule next poll
        intervalRef.current = setTimeout(poll, currentIntervalMs);
      } catch (error: any) {
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed > MAX_TIMEOUT_MS) {
          setState({
            isPolling: false,
            error: 'This is taking longer than expected. Pull to refresh or tap Retry.',
          });
          stopPolling();
          return;
        }

        const status = typeof error?.status === 'number' ? error.status : undefined;
        if (status === 404) {
          setState({ isPolling: false, error: 'Session not found.' });
          stopPolling();
          return;
        }

        // Keep polling on transient failures with backoff
        errorStreakRef.current += 1;
        const message = error?.message || 'Network issue—retrying…';
        setState({ isPolling: true, error: message });

        const jitter = Math.floor(Math.random() * 400);
        const errorBackoffMs = Math.min(
          Math.floor(currentIntervalMs * 1.6) + 750 + jitter * errorStreakRef.current,
          MAX_INTERVAL_MS
        );
        currentIntervalMs = Math.max(currentIntervalMs, errorBackoffMs);
        intervalRef.current = setTimeout(poll, currentIntervalMs);
      }
    }
    
    setState({ isPolling: true, error: null });
    poll();
    
    return () => {
      stopPolling();
    };
  }, [sessionId, enabled, retryKey]);
  
  function stopPolling() {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
  }
  
  function retry() {
    stopPolling();
    setState({ isPolling: false, error: null });
    setRetryKey((k) => k + 1);
  }

  return { ...state, retry };
}

