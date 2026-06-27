import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';

import SplashScreen from '../screens/SplashScreen';
import HomeScreen from '../screens/HomeScreen';
import RecordScreen from '../screens/RecordScreen';
import SessionDetailScreen from '../screens/SessionDetailScreen';
import SettingsScreen from '../screens/SettingsScreen';
import DiagnosticsScreen from '../screens/DiagnosticsScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Splash"
        screenOptions={{
          headerShown: true,
        }}
      >
        <Stack.Screen
          name="Splash"
          component={SplashScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Record"
          component={RecordScreen}
          options={{ title: 'Record Session' }}
        />
        <Stack.Screen
          name="SessionDetail"
          component={SessionDetailScreen}
          options={{ title: 'Session Detail' }}
        />
        <Stack.Screen
          name="Settings"
          component={SettingsScreen}
          options={{ title: 'Settings' }}
        />
        <Stack.Screen
          name="Diagnostics"
          component={DiagnosticsScreen}
          options={{ title: 'Diagnostics' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

