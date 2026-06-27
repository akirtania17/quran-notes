import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useStatsStore } from '../state/statsStore';
import { colors } from '../theme/colors';

type Props = {
  title: string;
  onSettingsPress?: () => void;
};

export default function ScreenHeader({ title, onSettingsPress }: Props) {
  const { xp, streakCount } = useStatsStore();
  
  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <Text style={styles.title}>{title}</Text>
        {onSettingsPress && (
          <TouchableOpacity onPress={onSettingsPress} style={styles.settingsButton}>
            <Text style={styles.settingsIcon}>⚙️</Text>
          </TouchableOpacity>
        )}
      </View>
      
      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>XP</Text>
          <Text style={styles.statValue}>{xp}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>🔥 Streak</Text>
          <Text style={styles.statValue}>{streakCount}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.goldDark,
  },
  settingsButton: {
    padding: 8,
  },
  settingsIcon: {
    fontSize: 24,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statBox: {
    backgroundColor: colors.goldSoft,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statLabel: {
    fontSize: 12,
    color: colors.goldDark,
    marginBottom: 2,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
  },
});

