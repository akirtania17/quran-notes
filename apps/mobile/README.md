# Quran Notes Mobile App

React Native mobile app built with Expo for recording, transcribing, translating, and summarizing Islamic lectures.

## Prerequisites

- Node.js 18+ and npm
- Expo Go app on your iPhone for development
- (Optional) Xcode for iOS builds

## Setup

1. **Install dependencies:**

```bash
cd apps/mobile
npm install
```

2. **Configure environment:**

Copy `.env.example` to `.env` and set your backend API URL:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.10:8000
```

Replace `192.168.1.10` with your computer's local IP address (ensure your phone and computer are on the same Wi-Fi network).

## Development

Start the development server:

```bash
npm start
```

Then scan the QR code with your iPhone camera or Expo Go app to launch the app.

### Development Features

- Hot reload enabled
- React DevTools support
- Network debugging

## Project Structure

```
src/
  api/           # API client and endpoints
  components/    # Reusable UI components
  constants/     # App constants
  hooks/         # Custom React hooks
  navigation/    # React Navigation setup
  screens/       # Main app screens
  state/         # Zustand stores
  storage/       # AsyncStorage helpers
  types/         # TypeScript types
  utils/         # Utility functions
  App.tsx        # Root component
```

## Key Features

- **Audio Recording**: Record lectures using expo-av
- **Session Management**: Upload and track processing status
- **XP & Streaks**: Local-only gamification (stored in AsyncStorage)
- **Privacy**: Anonymous device token, no auth required

## Build for TestFlight

See the main project README for EAS Build instructions.

## Tech Stack

- React Native + Expo
- TypeScript
- React Navigation
- Zustand (state management)
- AsyncStorage (local persistence)
- expo-av (audio recording)

