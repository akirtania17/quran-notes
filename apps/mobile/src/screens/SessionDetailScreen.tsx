import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Modal,
  Pressable,
} from 'react-native';
import { RootStackScreenProps } from '../navigation/types';
import { useSessionsStore } from '../state/sessionsStore';
import { useStatsStore } from '../state/statsStore';
import { useSessionPolling } from '../hooks/useSessionPolling';
import { getSession, retrySession } from '../api/sessions';
import { createNote, listNotes } from '../api/notes';
import { Highlight, Note } from '../types/contracts';
import StatusBadge from '../components/StatusBadge';
import PrimaryButton from '../components/PrimaryButton';
import SegmentedTabs from '../components/SegmentedTabs';
import SectionCard from '../components/SectionCard';
import { formatDate, formatDuration } from '../utils/format';
import { colors } from '../theme/colors';

type Tab = 'transcript' | 'translation' | 'summary' | 'notes';

// Important: must be a stable reference (do NOT inline `|| []` in Zustand selectors),
// otherwise React 19 can detect an unstable external store snapshot and loop.
const EMPTY_HIGHLIGHTS: Highlight[] = [];

function clampPct(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

function formatStepLabel(step: string | null | undefined): string | null {
  if (!step) return null;
  switch (step) {
    case 'queued':
      return 'Queued';
    case 'transcribing':
      return 'Transcribing';
    case 'ayah_linking':
      return 'Linking verse';
    case 'translating':
      return 'Translating';
    case 'summarizing':
      return 'Summarizing';
    case 'complete':
      return 'Complete';
    default:
      return step;
  }
}

function stepToPct(step: string | null | undefined): number {
  switch (step) {
    case 'queued':
      return 0;
    case 'transcribing':
      return 15;
    case 'ayah_linking':
      return 35;
    case 'translating':
      return 55;
    case 'summarizing':
      return 80;
    case 'complete':
      return 100;
    default:
      return 0;
  }
}

export default function SessionDetailScreen({
  route,
  navigation,
}: RootStackScreenProps<'SessionDetail'>) {
  const { sessionId } = route.params;
  const [activeTab, setActiveTab] = useState<Tab>('transcript');
  const [notes, setNotes] = useState<Note[]>([]);
  const [noteText, setNoteText] = useState('');
  const [isLoadingNotes, setIsLoadingNotes] = useState(false);
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [isRefreshingSession, setIsRefreshingSession] = useState(false);
  const [sessionLoadError, setSessionLoadError] = useState<string | null>(null);
  const [notesError, setNotesError] = useState<string | null>(null);
  
  const session = useSessionsStore((s) => s.getSession(sessionId));
  const updateSession = useSessionsStore((s) => s.updateSession);
  const setBookmarked = useSessionsStore((s) => s.setBookmarked);
  const highlightsFromStore = useSessionsStore((s) => s.highlightsBySessionId[sessionId]);
  const highlights: Highlight[] = highlightsFromStore ?? EMPTY_HIGHLIGHTS;
  const awardOpenCompleteXP = useStatsStore((s) => s.awardOpenCompleteXP);

  const shouldPoll = session?.status === 'processing' || session?.status === 'uploaded';
  const polling = useSessionPolling(sessionId, shouldPoll);
  
  useEffect(() => {
    loadSession();
  }, [sessionId]);
  
  useEffect(() => {
    if (session?.status === 'complete') {
      awardOpenCompleteXP(sessionId);
      loadNotes();
    }
  }, [session?.status]);
  
  async function loadSession() {
    setIsRefreshingSession(true);
    setSessionLoadError(null);
    try {
      const freshSession = await getSession(sessionId);
      updateSession(freshSession);
    } catch (error: any) {
      setSessionLoadError(error.message || 'Failed to load session');
    }
    setIsRefreshingSession(false);
  }

  async function handleRefresh() {
    polling.retry();
    await loadSession();
  }
  
  async function loadNotes() {
    setIsLoadingNotes(true);
    setNotesError(null);
    try {
      const fetchedNotes = await listNotes(sessionId);
      setNotes(fetchedNotes);
    } catch (error) {
      console.error('Failed to load notes:', error);
      setNotesError((error as any)?.message || 'Failed to load notes');
    } finally {
      setIsLoadingNotes(false);
    }
  }
  
  async function handleAddNote() {
    if (!noteText.trim()) return;
    
    setIsAddingNote(true);
    try {
      const note = await createNote({
        sessionId,
        text: noteText.trim(),
      });
      setNotes([note, ...notes]);
      setNoteText('');
      
      // Award XP
      const awardNoteXP = useStatsStore.getState().awardNoteXP;
      await awardNoteXP();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add note');
    } finally {
      setIsAddingNote(false);
    }
  }
  
  async function handleRetry() {
    try {
      await retrySession(sessionId);
      Alert.alert('Success', 'Processing restarted');
      loadSession();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to retry');
    }
  }

  async function handleToggleBookmark() {
    if (!session) return;
    try {
      await setBookmarked(sessionId, !session.bookmarked);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to update bookmark');
    }
  }

  
  if (!session) {
    return (
      <View style={styles.loadingContainer}>
        {sessionLoadError ? (
          <View style={styles.inlineError}>
            <Text style={styles.inlineErrorTitle}>Couldn't load session</Text>
            <Text style={styles.inlineErrorText}>{sessionLoadError}</Text>
            <PrimaryButton title="Retry" onPress={loadSession} />
          </View>
        ) : (
          <ActivityIndicator size="large" />
        )}
      </View>
    );
  }
  
  const tabs = [
    { key: 'transcript', label: 'Transcript' },
    { key: 'translation', label: 'Translation' },
    { key: 'summary', label: 'Summary' },
    { key: 'notes', label: 'Notes' },
  ];

  const stepLabel = formatStepLabel(session.processingStep);
  const pct = clampPct(session.progressPct ?? stepToPct(session.processingStep));
  const showProgressPanel = session.status === 'processing' || session.status === 'uploaded';
  const createdAtMs = new Date(session.createdAt).getTime();
  const isUploadedStale =
    session.status === 'uploaded' && Number.isFinite(createdAtMs) && Date.now() - createdAtMs > 3 * 60 * 1000;
  const stepItems = [
    { key: 'uploaded', label: 'Uploaded', done: true, current: false },
    {
      key: 'transcribing',
      label: 'Transcribing',
      done:
        session.processingStep === 'ayah_linking' ||
        session.processingStep === 'translating' ||
        session.processingStep === 'summarizing' ||
        session.processingStep === 'complete' ||
        session.status === 'complete',
      current: session.processingStep === 'transcribing',
    },
    {
      key: 'ayah_linking',
      label: 'Linking verse',
      done:
        session.processingStep === 'translating' ||
        session.processingStep === 'summarizing' ||
        session.processingStep === 'complete' ||
        session.status === 'complete',
      current: session.processingStep === 'ayah_linking',
    },
    {
      key: 'translating',
      label: 'Translating',
      done: session.processingStep === 'summarizing' || session.processingStep === 'complete' || session.status === 'complete',
      current: session.processingStep === 'translating',
    },
    {
      key: 'summarizing',
      label: 'Summarizing',
      done: session.processingStep === 'complete' || session.status === 'complete',
      current: session.processingStep === 'summarizing',
    },
  ];
  
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{session.title}</Text>
        <StatusBadge status={session.status} />
        <View style={styles.metaRow}>
          <Text style={styles.metaText}>{formatDate(session.createdAt)}</Text>
          {session.durationSeconds && (
            <Text style={styles.metaText}>{formatDuration(session.durationSeconds)}</Text>
          )}
        </View>

        <View style={styles.headerActions}>
          <View style={styles.headerActionsRow}>
            <PrimaryButton
              title={session.bookmarked ? 'Bookmarked' : 'Bookmark'}
              onPress={handleToggleBookmark}
              variant={session.bookmarked ? 'primary' : 'secondary'}
            />
            <PrimaryButton
              title={isRefreshingSession ? 'Refreshing...' : 'Refresh'}
              onPress={handleRefresh}
              loading={isRefreshingSession}
              variant="secondary"
            />
          </View>
        </View>
      </View>

      {!!polling.error && shouldPoll && (
        <View style={styles.pollError}>
          <Text style={styles.pollErrorTitle}>Trouble checking status</Text>
          <Text style={styles.pollErrorText}>{polling.error}</Text>
          <PrimaryButton title="Retry" onPress={handleRefresh} />
        </View>
      )}
      
      {showProgressPanel && (
        <View style={styles.processingCard}>
          <View style={styles.processingHeader}>
            <Text style={styles.processingTitle}>Processing</Text>
            <Text style={styles.processingSubtitle}>
              {stepLabel ? `${stepLabel}…` : 'Preparing…'} {`(${pct}%)`}
            </Text>
          </View>

          <View style={styles.progressBarTrack}>
            <View style={[styles.progressBarFill, { width: `${pct}%` }]} />
          </View>

          {session.processingStep === 'queued' && (
            <Text style={styles.processingHint}>Queued to start…</Text>
          )}

          {isUploadedStale && (
            <Text style={styles.processingStuckHint}>
              Still “Uploaded” after a few minutes. If the server restarted, tap “Start Processing” to resume.
            </Text>
          )}

          <View style={styles.stepList}>
            {stepItems.map((item) => (
              <View key={item.key} style={styles.stepRow}>
                <View
                  style={[
                    styles.stepDot,
                    item.done && styles.stepDotDone,
                    item.current && styles.stepDotCurrent,
                  ]}
                />
                <Text
                  style={[
                    styles.stepLabel,
                    item.done && styles.stepLabelDone,
                    item.current && styles.stepLabelCurrent,
                  ]}
                >
                  {item.label}
                </Text>
              </View>
            ))}
          </View>

          {polling.isPolling && (
            <View style={styles.processingFooter}>
              <ActivityIndicator size="small" color={colors.goldDark} />
              <Text style={styles.processingFooterText}>Checking for updates…</Text>
            </View>
          )}

          {session.status === 'uploaded' && (
            <View style={styles.processingActions}>
              <PrimaryButton
                title="Start Processing"
                onPress={handleRetry}
                variant="secondary"
              />
            </View>
          )}
        </View>
      )}

      <View style={styles.detectedVerseWrap}>
        <SectionCard title="Detected verse">
          {session.matchedSurah != null && session.matchedAyah != null && session.matchedAyahTextAr ? (
            <>
              <Text style={styles.detectedVerseRef}>
                Surah {session.matchedSurah}:{session.matchedAyah}
              </Text>
              <Text style={styles.detectedVerseArabic}>{session.matchedAyahTextAr}</Text>
              {typeof session.matchedConfidencePct === 'number' && (
                <Text style={styles.detectedVerseMeta}>
                  Confidence: {session.matchedConfidencePct >= 80 ? 'High' : session.matchedConfidencePct >= 55 ? 'Medium' : 'Low'} ({session.matchedConfidencePct}
                  %)
                </Text>
              )}
              {session.matchedCandidates && session.matchedCandidates.length > 1 && (
                <View style={styles.altWrap}>
                  <Text style={styles.altTitle}>Other possibilities</Text>
                  {session.matchedCandidates.slice(1, 4).map((c) => (
                    <Text key={`${c.surah}:${c.ayah}`} style={styles.altItem}>
                      Surah {c.surah}:{c.ayah} ({c.scorePct}%)
                    </Text>
                  ))}
                </View>
              )}
            </>
          ) : session.matchedMethod == null && (session.status === 'processing' || session.status === 'uploaded') ? (
            <Text style={styles.emptyText}>Detecting verse…</Text>
          ) : (
            <Text style={styles.emptyText}>No verse detected</Text>
          )}
        </SectionCard>
      </View>
      
      {session.status === 'failed' && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            {session.errorMessage
              ? `${session.errorMessage}${stepLabel ? `\n\nFailed during ${stepLabel}.` : ''}`
              : `Processing failed${stepLabel ? ` during ${stepLabel}.` : ''}`}
          </Text>
          <PrimaryButton title="Retry" onPress={handleRetry} style={styles.retryButton} />
        </View>
      )}
      
      {session.status === 'complete' && (
        <View style={styles.content}>
          <SegmentedTabs tabs={tabs} activeTab={activeTab} onTabChange={(key) => setActiveTab(key as Tab)} />
          
          <View style={styles.tabContent}>
            {activeTab === 'transcript' && (
              <SectionCard title="Transcript">
                {session.transcript ? (
                  <Text style={styles.bodyText}>{session.transcript}</Text>
                ) : (
                  <Text style={styles.emptyText}>No transcript available</Text>
                )}
                {session.sourceLanguage && (
                  <Text style={styles.metaText}>Language: {session.sourceLanguage}</Text>
                )}
              </SectionCard>
            )}
            
            {activeTab === 'translation' && (
              <SectionCard title="Translation">
                {session.translation ? (
                  <Text style={styles.bodyText}>{session.translation}</Text>
                ) : (
                  <Text style={styles.emptyText}>No translation available</Text>
                )}
                <Text style={styles.metaText}>Target: {session.targetLanguage}</Text>
              </SectionCard>
            )}
            
            {activeTab === 'summary' && (
              <SectionCard title="Summary">
                {session.summaryBullets && session.summaryBullets.length > 0 ? (
                  session.summaryBullets.map((bullet, idx) => (
                    <View key={idx} style={styles.bulletItem}>
                      <Text style={styles.bullet}>•</Text>
                      <Text style={styles.bodyText}>{bullet}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.emptyText}>No summary available</Text>
                )}
              </SectionCard>
            )}
            
            {activeTab === 'notes' && (
              <>
                <SectionCard title="Add Note">
                  <TextInput
                    style={styles.noteInput}
                    placeholder="Write a note..."
                    value={noteText}
                    onChangeText={setNoteText}
                    multiline
                  />
                  <PrimaryButton
                    title="Add Note (+1 XP)"
                    onPress={handleAddNote}
                    disabled={!noteText.trim()}
                    loading={isAddingNote}
                  />
                </SectionCard>
                
                <SectionCard title={`My Notes (${notes.length})`}>
                  {isLoadingNotes ? (
                    <ActivityIndicator />
                  ) : notesError ? (
                    <View style={styles.inlineError}>
                      <Text style={styles.inlineErrorTitle}>Couldn't load notes</Text>
                      <Text style={styles.inlineErrorText}>{notesError}</Text>
                      <PrimaryButton title="Retry" onPress={loadNotes} variant="secondary" />
                    </View>
                  ) : notes.length > 0 ? (
                    notes.map((note) => (
                      <View key={note.id} style={styles.noteItem}>
                        <Text style={styles.noteText}>{note.text}</Text>
                        <Text style={styles.noteDate}>{formatDate(note.createdAt)}</Text>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.emptyText}>No notes yet</Text>
                  )}
                </SectionCard>
              </>
            )}

          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  header: {
    backgroundColor: colors.surface,
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  headerActions: {
    marginTop: 14,
  },
  headerActionsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  metaText: {
    fontSize: 13,
    color: colors.mutedText,
    marginTop: 4,
  },
  processingCard: {
    backgroundColor: colors.surface,
    marginHorizontal: 20,
    marginTop: 16,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  processingHeader: {
    marginBottom: 12,
  },
  processingTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 4,
  },
  processingSubtitle: {
    fontSize: 14,
    color: colors.mutedText,
  },
  processingHint: {
    fontSize: 13,
    color: colors.mutedText,
    marginTop: 10,
  },
  processingStuckHint: {
    fontSize: 13,
    color: colors.mutedText,
    marginTop: 10,
  },
  progressBarTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.goldSoft,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.goldDark,
  },
  stepList: {
    marginTop: 14,
    gap: 10,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  stepDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#D0D7E2',
  },
  stepDotDone: {
    backgroundColor: '#2E7D32',
  },
  stepDotCurrent: {
    backgroundColor: colors.goldDark,
  },
  stepLabel: {
    fontSize: 14,
    color: colors.mutedText,
  },
  stepLabelDone: {
    color: '#2E7D32',
    fontWeight: '600',
  },
  stepLabelCurrent: {
    color: colors.goldDark,
    fontWeight: '700',
  },
  processingFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 14,
  },
  processingFooterText: {
    fontSize: 13,
    color: colors.mutedText,
  },
  processingActions: {
    marginTop: 12,
    maxWidth: 200,
  },
  errorContainer: {
    padding: 20,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#D32F2F',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    minWidth: 120,
  },
  pollError: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 20,
    marginTop: 16,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F3C6C6',
  },
  pollErrorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#D32F2F',
    marginBottom: 6,
  },
  pollErrorText: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 12,
  },
  inlineError: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F3C6C6',
    width: '100%',
  },
  inlineErrorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#D32F2F',
    marginBottom: 6,
  },
  inlineErrorText: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 12,
  },
  content: {
    padding: 20,
  },
  detectedVerseWrap: {
    marginHorizontal: 20,
    marginTop: 16,
  },
  detectedVerseRef: {
    fontSize: 13,
    color: colors.mutedText,
    marginBottom: 10,
  },
  detectedVerseArabic: {
    fontSize: 20,
    lineHeight: 32,
    color: colors.text,
    textAlign: 'right',
    marginBottom: 10,
  },
  detectedVerseMeta: {
    fontSize: 13,
    color: colors.mutedText,
  },
  altWrap: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 10,
    gap: 6,
  },
  altTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
  },
  altItem: {
    fontSize: 13,
    color: colors.mutedText,
  },
  tabContent: {
    marginTop: 16,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#000000',
  },
  emptyText: {
    fontSize: 15,
    color: '#999999',
    fontStyle: 'italic',
  },
  bulletItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  bullet: {
    fontSize: 15,
    marginRight: 8,
    color: '#000000',
  },
  noteInput: {
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 12,
  },
  noteItem: {
    backgroundColor: '#F9F9F9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  noteText: {
    fontSize: 15,
    color: '#000000',
    marginBottom: 4,
  },
  noteDate: {
    fontSize: 12,
    color: '#999999',
  },
});

