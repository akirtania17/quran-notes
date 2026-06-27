import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import RootNavigator from './navigation/RootNavigator';
import { useStatsStore } from './state/statsStore';
import { useSettingsStore } from './state/settingsStore';

export default function App() {
  const loadStats = useStatsStore((s) => s.loadStats);
  const loadSettings = useSettingsStore((s) => s.loadSettings);
  
  useEffect(() => {
    // Initialize stores on app launch
    loadStats();
    loadSettings();
  }, []);
  
  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <RootNavigator />
    </SafeAreaProvider>
  );
}

