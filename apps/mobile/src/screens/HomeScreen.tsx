import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { RootStackScreenProps } from '../navigation/types';
import { useSessionsStore } from '../state/sessionsStore';
import { useStatsStore } from '../state/statsStore';
import { useSettingsStore } from '../state/settingsStore';
import { listSessions } from '../api/sessions';
import { listLanguages } from '../api/languages';
import ScreenHeader from '../components/ScreenHeader';
import StatusBadge from '../components/StatusBadge';
import PrimaryButton from '../components/PrimaryButton';
import SegmentedTabs from '../components/SegmentedTabs';
import { formatDate, formatDuration } from '../utils/format';
import { colors } from '../theme/colors';

export default function HomeScreen({ navigation }: RootStackScreenProps<'Home'>) {
  const { sessions, isLoading, error, setLoading, setSessions, setError } = useSessionsStore();
  const { xp, streakCount, loadStats } = useStatsStore();
  const { loadSettings, setLanguages } = useSettingsStore();
  const [filter, setFilter] = useState<'all' | 'bookmarked'>('all');

  const filteredSessions = useMemo(() => {
    if (filter === 'bookmarked') {
      return sessions.filter((s) => s.bookmarked);
    }
    return sessions;
  }, [sessions, filter]);
  
  useEffect(() => {
    loadInitialData();
  }, []);
  
  async function loadInitialData() {
    try {
      await Promise.all([loadStats(), loadSettings()]);
      await fetchSessions();
      await fetchLanguages();
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  }
  
  async function fetchSessions() {
    setLoading(true);
    setError(null);
    try {
      const response = await listSessions(0, 20);
      setSessions(response.items, response.next_offset);
    } catch (error: any) {
      setError(error.message || 'Failed to load sessions');
    }
  }
  
  async function fetchLanguages() {
    try {
      const languages = await listLanguages();
      setLanguages(languages);
    } catch (error) {
      console.error('Failed to load languages:', error);
    }
  }
  
  function handleSessionPress(sessionId: string) {
    navigation.navigate('SessionDetail', { sessionId });
  }
  
  function handleRecordPress() {
    navigation.navigate('Record');
  }
  
  function handleSettingsPress() {
    navigation.navigate('Settings');
  }
  
  return (
    <View style={styles.container}>
      <ScreenHeader title="Quran Notes" onSettingsPress={handleSettingsPress} />
      
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{xp}</Text>
          <Text style={styles.statLabel}>XP</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{streakCount}</Text>
          <Text style={styles.statLabel}>Day Streak</Text>
        </View>
      </View>
      
      <View style={styles.content}>
        <PrimaryButton
          title="🎤 Record New Session"
          onPress={handleRecordPress}
          style={styles.recordButton}
        />

        <SegmentedTabs
          tabs={[
            { key: 'all', label: 'All' },
            { key: 'bookmarked', label: 'Bookmarked' },
          ]}
          activeTab={filter}
          onTabChange={(key) => setFilter(key as any)}
        />

        {error && !isLoading && (
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>Couldn't load sessions</Text>
            <Text style={styles.errorText}>{error}</Text>
            <PrimaryButton title="Retry" onPress={fetchSessions} />
          </View>
        )}
        
        {filteredSessions.length === 0 && !isLoading && !error ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>
              {filter === 'bookmarked' ? 'No bookmarked sessions' : 'No sessions yet'}
            </Text>
            <Text style={styles.emptySubtext}>
              {filter === 'bookmarked'
                ? 'Bookmark a session from its details screen to see it here'
                : 'Tap the button above to record your first session'}
            </Text>
          </View>
        ) : (
          <FlatList
            data={filteredSessions}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.sessionCard}
                onPress={() => handleSessionPress(item.id)}
              >
                <View style={styles.sessionHeader}>
                  <View style={styles.sessionTitleRow}>
                    <Text style={styles.sessionTitle} numberOfLines={2}>
                      {item.title}
                    </Text>
                    {item.bookmarked && <Text style={styles.bookmarkBadge}>Saved</Text>}
                  </View>
                  <StatusBadge status={item.status} />
                </View>
                <View style={styles.sessionMeta}>
                  <Text style={styles.sessionMetaText}>
                    {formatDate(item.createdAt)}
                  </Text>
                  {item.durationSeconds && (
                    <Text style={styles.sessionMetaText}>
                      {formatDuration(item.durationSeconds)}
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
            )}
            refreshControl={
              <RefreshControl refreshing={isLoading} onRefresh={fetchSessions} />
            }
            contentContainerStyle={styles.listContent}
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    paddingVertical: 16,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  statItem: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.goldDark,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: colors.mutedText,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  recordButton: {
    marginBottom: 20,
  },
  sessionTitleRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginRight: 8,
  },
  bookmarkBadge: {
    fontSize: 12,
    color: colors.goldDark,
    backgroundColor: colors.goldSoft,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    overflow: 'hidden',
  },
  errorCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F3C6C6',
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#D32F2F',
    marginBottom: 6,
  },
  errorText: {
    fontSize: 14,
    color: colors.mutedText,
    marginBottom: 12,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.mutedText,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.subtleText,
    textAlign: 'center',
  },
  listContent: {
    paddingBottom: 20,
  },
  sessionCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  sessionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
  },
  sessionMeta: {
    flexDirection: 'row',
    gap: 12,
  },
  sessionMetaText: {
    fontSize: 13,
    color: colors.mutedText,
  },
});

