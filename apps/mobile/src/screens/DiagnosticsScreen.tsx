import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import PrimaryButton from '../components/PrimaryButton';
import SectionCard from '../components/SectionCard';
import { apiClient } from '../api/client';
import { getClientId } from '../storage/asyncStorage';
import { useSettingsStore } from '../state/settingsStore';
import { getDefaultApiBaseUrl } from '../constants/api';
import { colors } from '../theme/colors';

type HealthResponse = {
  status: string;
  environment?: string;
  storage_backend?: string;
  version?: string;
  git_sha?: string | null;
};

export default function DiagnosticsScreen() {
  const { apiBaseUrl } = useSettingsStore();
  const [clientId, setClientId] = useState<string>('');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveBaseUrl = useMemo(() => apiBaseUrl || getDefaultApiBaseUrl(), [apiBaseUrl]);

  useEffect(() => {
    loadClientId();
    checkHealth();
  }, []);

  async function loadClientId() {
    const id = await getClientId();
    setClientId(id);
  }

  async function checkHealth() {
    setLoading(true);
    setError(null);
    try {
      const resp = await apiClient.get<HealthResponse>('/v1/health', 6000);
      setHealth(resp);
    } catch (e: any) {
      setError(e?.message || 'Failed to reach backend');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }

  function renderHealth() {
    if (loading) return <ActivityIndicator />;
    if (error) return <Text style={styles.errorText}>{error}</Text>;
    if (!health) return <Text style={styles.muted}>No data yet.</Text>;
    return (
      <View style={styles.healthList}>
        <Text style={styles.healthRow}>status: {health.status}</Text>
        {health.environment && <Text style={styles.healthRow}>env: {health.environment}</Text>}
        {health.storage_backend && <Text style={styles.healthRow}>storage: {health.storage_backend}</Text>}
        {health.version && <Text style={styles.healthRow}>version: {health.version}</Text>}
        {health.git_sha && <Text style={styles.healthRow}>git_sha: {health.git_sha}</Text>}
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <SectionCard title="App info">
        <Text style={styles.label}>Effective API base URL</Text>
        <Text style={styles.value}>{effectiveBaseUrl}</Text>

        <Text style={styles.label}>Client ID</Text>
        <Text style={styles.value}>{clientId}</Text>
      </SectionCard>

      <SectionCard title="Backend health">
        {renderHealth()}
        <View style={styles.buttonRow}>
          <PrimaryButton title="Check health" onPress={checkHealth} loading={loading} />
        </View>
      </SectionCard>

      <SectionCard title="Tips for reporting">
        <Text style={styles.muted}>1) Include this screen in screenshots.</Text>
        <Text style={styles.muted}>2) Note the time and action you took.</Text>
        <Text style={styles.muted}>3) Share the request id if shown in errors.</Text>
      </SectionCard>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 20,
    gap: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginTop: 6,
  },
  value: {
    fontSize: 14,
    color: colors.mutedText,
    marginTop: 4,
  },
  muted: {
    fontSize: 14,
    color: colors.mutedText,
    marginTop: 4,
  },
  errorText: {
    fontSize: 14,
    color: '#D32F2F',
  },
  healthList: {
    gap: 6,
  },
  healthRow: {
    fontSize: 14,
    color: colors.text,
  },
  buttonRow: {
    marginTop: 12,
  },
});

