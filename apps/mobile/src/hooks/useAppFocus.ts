import { useEffect } from 'react';
import { AppState, AppStateStatus } from 'react-native';

type AppFocusCallback = () => void;

export function useAppFocus(onFocus: AppFocusCallback) {
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      if (nextAppState === 'active') {
        onFocus();
      }
    });
    
    return () => {
      subscription.remove();
    };
  }, [onFocus]);
}

