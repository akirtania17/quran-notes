import { create } from 'zustand';
import { Stats } from '../types/contracts';
import { getStats, saveStats } from '../storage/asyncStorage';
import { getTodayString, isYesterday } from '../utils/date';

type StatsState = Stats & {
  isLoaded: boolean;
  
  // Actions
  loadStats: () => Promise<void>;
  awardUploadXP: (sessionId: string) => Promise<void>;
  awardOpenCompleteXP: (sessionId: string) => Promise<void>;
  awardNoteXP: () => Promise<void>;
};

const MAX_OPENED_IDS = 200;

export const useStatsStore = create<StatsState>((set, get) => ({
  xp: 0,
  streakCount: 0,
  lastStreakDate: null,
  openedCompleteSessionIds: [],
  uploadedSessionIds: [],
  isLoaded: false,
  
  loadStats: async () => {
    const stats = await getStats();
    set({ ...stats, isLoaded: true });
  },
  
  awardUploadXP: async (sessionId: string) => {
    const state = get();
    if (state.uploadedSessionIds.includes(sessionId)) {
      return;
    }
    const newXp = state.xp + 5;
    const newUploaded = [sessionId, ...(state.uploadedSessionIds || [])].slice(0, MAX_OPENED_IDS);
    const newStats = { ...state, xp: newXp, uploadedSessionIds: newUploaded };
    await saveStats(newStats);
    set(newStats);
  },
  
  awardOpenCompleteXP: async (sessionId: string) => {
    const state = get();
    
    // Check if already opened this session
    if (state.openedCompleteSessionIds.includes(sessionId)) {
      return;
    }
    
    // Award XP
    const newXp = state.xp + 2;
    
    // Update streak
    const today = getTodayString();
    let newStreakCount = state.streakCount;
    let newLastStreakDate = today;
    
    if (state.lastStreakDate === today) {
      // Already counted today
      newStreakCount = state.streakCount;
      newLastStreakDate = state.lastStreakDate;
    } else if (state.lastStreakDate && isYesterday(state.lastStreakDate)) {
      // Continue streak
      newStreakCount = state.streakCount + 1;
    } else {
      // Start new streak
      newStreakCount = 1;
    }
    
    // Add to opened list (cap at MAX_OPENED_IDS)
    const newOpenedIds = [sessionId, ...state.openedCompleteSessionIds].slice(0, MAX_OPENED_IDS);
    
    const newStats = {
      ...state,
      xp: newXp,
      streakCount: newStreakCount,
      lastStreakDate: newLastStreakDate,
      openedCompleteSessionIds: newOpenedIds,
    };
    
    await saveStats(newStats);
    set(newStats);
  },
  
  awardNoteXP: async () => {
    const state = get();
    const newXp = state.xp + 1;
    const newStats = { ...state, xp: newXp };
    await saveStats(newStats);
    set({ xp: newXp });
  },
}));

