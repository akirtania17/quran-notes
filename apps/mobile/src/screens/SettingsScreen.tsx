import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, Alert } from 'react-native';
import { NavigationProp, useNavigation } from '@react-navigation/native';
import { useSettingsStore } from '../state/settingsStore';
import { useSessionsStore } from '../state/sessionsStore';
import { useStatsStore } from '../state/statsStore';
import { RootStackParamList } from '../navigation/types';
import SectionCard from '../components/SectionCard';
import { Picker } from '@react-native-picker/picker';
import PrimaryButton from '../components/PrimaryButton';
import { APP_ENV, DEFAULT_API_BASE_URL, getDefaultApiBaseUrl } from '../constants/api';
import { clearAppData } from '../storage/asyncStorage';
import { colors } from '../theme/colors';

export default function SettingsScreen() {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const { languages, defaultTargetLanguage, apiBaseUrl, lastAutoResetApiBaseUrl, setDefaultLanguage, setApiBaseUrl, resetApiBaseUrl } =
    useSettingsStore();
  const clearSessions = useSessionsStore((s) => s.clearSessions);
  const loadStats = useStatsStore((s) => s.loadStats);
  const loadSettings = useSettingsStore((s) => s.loadSettings);

  const [apiBaseUrlDraft, setApiBaseUrlDraft] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  useEffect(() => {
    setApiBaseUrlDraft(apiBaseUrl || '');
  }, [apiBaseUrl]);

  // Note: compute dynamically so it reflects the current Expo dev host when the user taps Reset.
  const effectiveBaseUrl = useMemo(() => apiBaseUrl || getDefaultApiBaseUrl() || DEFAULT_API_BASE_URL, [apiBaseUrl]);
  const isApiEditable = APP_ENV === 'dev' || __DEV__;

  async function handleSaveApiBaseUrl() {
    try {
      await setApiBaseUrl(apiBaseUrlDraft);
      Alert.alert('Saved', 'API Base URL updated');
    } catch (error: any) {
      Alert.alert('Error', error?.message || 'Failed to save API Base URL');
    }
  }

  async function handleResetApiBaseUrl() {
    try {
      await resetApiBaseUrl();
      Alert.alert('Reset', 'API Base URL reset to default');
    } catch (error: any) {
      Alert.alert('Error', error?.message || 'Failed to reset API Base URL');
    }
  }

  async function handleResetLocalData() {
    setIsResetting(true);
    try {
      await clearAppData({ resetClientId: false });
      clearSessions();
      await Promise.all([loadStats(), loadSettings()]);
      Alert.alert('Cleared', 'Local data cleared. Stats and API overrides reset.');
    } catch (error: any) {
      Alert.alert('Error', error?.message || 'Failed to clear local data');
    } finally {
      setIsResetting(false);
    }
  }
  
  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <SectionCard title="Default Target Language">
          <Text style={styles.description}>
            This language will be pre-selected when creating new sessions
          </Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={defaultTargetLanguage}
              onValueChange={(value) => setDefaultLanguage(value)}
              style={styles.picker}
            >
              {languages.map((lang) => (
                <Picker.Item key={lang.code} label={lang.label} value={lang.code} />
              ))}
            </Picker>
          </View>
        </SectionCard>

        <SectionCard title="API (Dev)">
          {isApiEditable ? (
            <>
              {!!lastAutoResetApiBaseUrl && (
                <View style={styles.warningBox}>
                  <Text style={styles.warningTitle}>API URL auto-reset</Text>
                  <Text style={styles.warningText}>
                    Your previous API Base URL was unreachable and has been reset to the default.
                  </Text>
                  <Text style={styles.warningText}>
                    Previous: <Text style={styles.mono}>{lastAutoResetApiBaseUrl}</Text>
                  </Text>
                </View>
              )}
              <Text style={styles.description}>
                Used for all requests to the backend. On a physical device, use your computer's LAN IP (not
                localhost).
              </Text>

              <Text style={styles.label}>API Base URL</Text>
              <TextInput
                style={styles.input}
                placeholder={DEFAULT_API_BASE_URL}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
                value={apiBaseUrlDraft}
                onChangeText={setApiBaseUrlDraft}
              />

              <Text style={styles.helpText}>Examples:</Text>
              <Text style={styles.helpText}>- http://192.168.1.10:8000</Text>
              <Text style={styles.helpText}>- http://10.0.2.2:8000 (Android emulator)</Text>
              <Text style={styles.helpText}>- http://localhost:8000 (iOS simulator)</Text>

              <Text style={styles.currentValue}>
                Current effective URL: <Text style={styles.mono}>{effectiveBaseUrl}</Text>
              </Text>

              <View style={styles.row}>
                <PrimaryButton title="Save" onPress={handleSaveApiBaseUrl} style={styles.rowButton} />
                <PrimaryButton
                  title="Reset"
                  onPress={handleResetApiBaseUrl}
                  variant="secondary"
                  style={styles.rowButton}
                />
              </View>
            </>
          ) : (
            <>
              <Text style={styles.description}>
                This build is pinned to the tester backend URL. If uploads fail, share the effective URL with support.
              </Text>
              <Text style={styles.currentValue}>
                Current effective URL: <Text style={styles.mono}>{effectiveBaseUrl}</Text>
              </Text>
            </>
          )}
        </SectionCard>
        
        <SectionCard title="Diagnostics">
          <Text style={styles.description}>
            View device id, effective API URL, and backend health. Share this info when reporting issues.
          </Text>
          <PrimaryButton title="Open Diagnostics" onPress={() => navigation.navigate('Diagnostics')} />
        </SectionCard>
        
        <SectionCard title="Privacy">
          <Text style={styles.description}>
            All sessions and notes are stored locally on your device using an anonymous
            device token. No personal information is collected or shared.
          </Text>
          <Text style={styles.description}>
            XP and streak data are stored locally and will reset if you reinstall the app.
          </Text>
        </SectionCard>
        
        <SectionCard title="About">
          <Text style={styles.description}>
            Quran Notes helps you transcribe, translate, and summarize Islamic lectures
            and study sessions.
          </Text>
          <Text style={styles.versionText}>Version 1.0.0</Text>
        </SectionCard>

        <SectionCard title="Danger zone">
          <Text style={styles.description}>
            Clear locally stored stats, language preference, and API overrides. Sessions will also be cleared from this
            device (they remain on the server).
          </Text>
          <PrimaryButton
            title={isResetting ? 'Clearing…' : 'Reset local data'}
            onPress={handleResetLocalData}
            loading={isResetting}
            variant="danger"
          />
        </SectionCard>
      </View>
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
  },
  description: {
    fontSize: 14,
    color: colors.mutedText,
    lineHeight: 20,
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    marginBottom: 12,
  },
  helpText: {
    fontSize: 13,
    color: colors.mutedText,
    marginBottom: 4,
  },
  currentValue: {
    fontSize: 13,
    color: colors.mutedText,
    marginTop: 10,
    marginBottom: 12,
  },
  mono: {
    fontFamily: 'monospace',
    color: colors.text,
  },
  warningBox: {
    backgroundColor: '#FFF7E6',
    borderWidth: 1,
    borderColor: '#F5D08A',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#8A5A00',
    marginBottom: 4,
  },
  warningText: {
    fontSize: 13,
    color: '#8A5A00',
    marginTop: 2,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  rowButton: {
    flex: 1,
  },
  pickerContainer: {
    backgroundColor: colors.background,
    borderRadius: 8,
    marginTop: 8,
  },
  picker: {
    // Platform-specific styling
  },
  versionText: {
    fontSize: 12,
    color: colors.subtleText,
    marginTop: 8,
  },
});

