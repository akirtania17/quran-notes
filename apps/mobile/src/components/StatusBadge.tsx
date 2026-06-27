import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SessionStatus } from '../types/contracts';
import { colors } from '../theme/colors';

type Props = {
  status: SessionStatus;
};

export default function StatusBadge({ status }: Props) {
  const config = getStatusConfig(status);
  
  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <Text style={[styles.text, { color: config.color }]}>{config.label}</Text>
    </View>
  );
}

function getStatusConfig(status: SessionStatus) {
  switch (status) {
    case 'uploaded':
      return { label: 'Uploaded', bg: '#F0F0F0', color: '#666666' };
    case 'processing':
      return { label: 'Processing...', bg: colors.goldSoft, color: colors.goldDark };
    case 'complete':
      return { label: 'Complete', bg: colors.successSoft, color: colors.success };
    case 'failed':
      return { label: 'Failed', bg: colors.dangerSoft, color: colors.danger };
  }
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
  },
});

