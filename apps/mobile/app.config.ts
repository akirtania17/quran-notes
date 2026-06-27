import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'Quran Notes',
  slug: 'quran-notes',
  version: '1.0.0',
  plugins: ['expo-asset'],
  orientation: 'portrait',
  // NOTE: Keep icon/splash assets out of the config for local dev if you don't have them yet.
  // Expo Go can run without them; missing files can spam warnings and confuse debugging.
  userInterfaceStyle: 'light',
  splash: undefined,
  assetBundlePatterns: ['**/*'],
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'com.qurannotes.app',
    infoPlist: {
      NSMicrophoneUsageDescription: 'This app needs access to your microphone to record audio lectures.',
      NSSpeechRecognitionUsageDescription: 'This app needs speech recognition to transcribe your recordings.',
    },
  },
  android: {
    adaptiveIcon: undefined,
    package: 'com.qurannotes.app',
    permissions: ['RECORD_AUDIO'],
  },
  web: {
    favicon: undefined,
  },
  extra: {
    // API base URL is controlled by EXPO_PUBLIC_API_BASE_URL; no baked-in LAN IP for tester builds.
    apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL,
    eas: {
      projectId: 'cf77122b-422e-4755-8043-df325be2f2d0',
    },
  },
});

