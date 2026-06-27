import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

type Tab = {
  key: string;
  label: string;
};

type Props = {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (key: string) => void;
};

export default function SegmentedTabs({ tabs, activeTab, onTabChange }: Props) {
  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const isActive = tab.key === activeTab;
        return (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, isActive && styles.activeTab]}
            onPress={() => onTabChange(tab.key)}
          >
            <Text style={[styles.tabText, isActive && styles.activeTabText]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: colors.goldSoft,
    borderRadius: 12,
    padding: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: colors.surface,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.mutedText,
  },
  activeTabText: {
    color: colors.goldDark,
  },
});

