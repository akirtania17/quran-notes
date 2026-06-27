import { useState } from 'react';
import { Audio } from 'expo-av';

type RecordingState = {
  isRecording: boolean;
  isPaused: boolean;
  recordingUri: string | null;
  durationSeconds: number;
};

export function useAudioRecorder() {
  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    recordingUri: null,
    durationSeconds: 0,
  });
  
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  
  async function requestPermission(): Promise<boolean> {
    const { status } = await Audio.requestPermissionsAsync();
    return status === 'granted';
  }
  
  async function startRecording(): Promise<void> {
    try {
      const hasPermission = await requestPermission();
      if (!hasPermission) {
        throw new Error('Microphone permission not granted');
      }
      
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(newRecording);
      setState((s) => ({ ...s, isRecording: true, isPaused: false }));
      
      // Update duration every second
      newRecording.setOnRecordingStatusUpdate((status) => {
        if (status.isRecording) {
          setState((s) => ({
            ...s,
            durationSeconds: Math.floor((status.durationMillis || 0) / 1000),
          }));
        }
      });
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }
  
  async function stopRecording(): Promise<void> {
    if (!recording) return;
    
    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      
      setRecording(null);
      setState((s) => ({
        ...s,
        isRecording: false,
        isPaused: false,
        recordingUri: uri,
      }));
      
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });
    } catch (error) {
      console.error('Failed to stop recording:', error);
      throw error;
    }
  }
  
  async function pauseRecording(): Promise<void> {
    if (!recording) return;
    
    try {
      await recording.pauseAsync();
      setState((s) => ({ ...s, isPaused: true }));
    } catch (error) {
      console.error('Failed to pause recording:', error);
    }
  }
  
  async function resumeRecording(): Promise<void> {
    if (!recording) return;
    
    try {
      await recording.startAsync();
      setState((s) => ({ ...s, isPaused: false }));
    } catch (error) {
      console.error('Failed to resume recording:', error);
    }
  }
  
  async function playRecording(): Promise<void> {
    if (!state.recordingUri) return;
    
    try {
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: state.recordingUri },
        { shouldPlay: true }
      );
      setSound(newSound);
    } catch (error) {
      console.error('Failed to play recording:', error);
    }
  }
  
  async function stopPlayback(): Promise<void> {
    if (!sound) return;
    
    try {
      await sound.stopAsync();
      await sound.unloadAsync();
      setSound(null);
    } catch (error) {
      console.error('Failed to stop playback:', error);
    }
  }
  
  function reset(): void {
    setState({
      isRecording: false,
      isPaused: false,
      recordingUri: null,
      durationSeconds: 0,
    });
  }
  
  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    playRecording,
    stopPlayback,
    reset,
  };
}

