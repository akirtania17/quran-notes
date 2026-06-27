import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { RootStackScreenProps } from '../navigation/types';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useUploadSession } from '../hooks/useUploadSession';
import { useSettingsStore } from '../state/settingsStore';
import PrimaryButton from '../components/PrimaryButton';
import { Picker } from '@react-native-picker/picker';
import { formatDuration } from '../utils/format';
import { colors } from '../theme/colors';

export default function RecordScreen({ navigation }: RootStackScreenProps<'Record'>) {
  const [title, setTitle] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('en');
  
  const { languages, defaultTargetLanguage } = useSettingsStore();
  const {
    isRecording,
    isPaused,
    recordingUri,
    durationSeconds,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    playRecording,
    reset: resetRecorder,
  } = useAudioRecorder();
  
  const { isUploading, error: uploadError, upload, reset: resetUpload } = useUploadSession();
  
  React.useEffect(() => {
    setTargetLanguage(defaultTargetLanguage);
  }, [defaultTargetLanguage]);
  
  async function handleStartRecording() {
    try {
      await startRecording();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to start recording');
    }
  }
  
  async function handleStopRecording() {
    try {
      await stopRecording();
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to stop recording');
    }
  }
  
  async function handleUpload() {
    if (!title.trim()) {
      Alert.alert('Error', 'Please enter a title');
      return;
    }
    
    if (!recordingUri) {
      Alert.alert('Error', 'No recording found');
      return;
    }
    
    const session = await upload({
      title: title.trim(),
      targetLanguage,
      durationSeconds,
      audioUri: recordingUri,
    });
    
    if (session) {
      Alert.alert('Success', 'Session uploaded successfully!', [
        {
          text: 'OK',
          onPress: () => {
            resetRecorder();
            resetUpload();
            setTitle('');
            navigation.navigate('SessionDetail', { sessionId: session.id });
          },
        },
      ]);
    }
  }
  
  function handleCancel() {
    resetRecorder();
    resetUpload();
    setTitle('');
    navigation.goBack();
  }
  
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.timerContainer}>
        <Text style={styles.timerText}>{formatDuration(durationSeconds)}</Text>
        {isRecording && !isPaused && <Text style={styles.recordingIndicator}>● REC</Text>}
        {isPaused && <Text style={styles.pausedIndicator}>⏸ PAUSED</Text>}
      </View>
      
      <View style={styles.controlsContainer}>
        {!isRecording && !recordingUri && (
          <PrimaryButton
            title="Start Recording"
            onPress={handleStartRecording}
            style={styles.button}
          />
        )}
        
        {isRecording && !isPaused && (
          <>
            <PrimaryButton
              title="Pause"
              onPress={pauseRecording}
              variant="secondary"
              style={styles.button}
            />
            <PrimaryButton
              title="Stop"
              onPress={handleStopRecording}
              variant="danger"
              style={styles.button}
            />
          </>
        )}
        
        {isRecording && isPaused && (
          <>
            <PrimaryButton
              title="Resume"
              onPress={resumeRecording}
              style={styles.button}
            />
            <PrimaryButton
              title="Stop"
              onPress={handleStopRecording}
              variant="danger"
              style={styles.button}
            />
          </>
        )}
        
        {recordingUri && !isRecording && (
          <>
            <PrimaryButton
              title="Play Recording"
              onPress={playRecording}
              variant="secondary"
              style={styles.button}
            />
            <PrimaryButton
              title="Record Again"
              onPress={() => {
                resetRecorder();
                handleStartRecording();
              }}
              variant="secondary"
              style={styles.button}
            />
          </>
        )}
      </View>
      
      {recordingUri && !isRecording && (
        <View style={styles.formContainer}>
          <Text style={styles.label}>Title *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter session title"
            value={title}
            onChangeText={setTitle}
          />
          
          <Text style={styles.label}>Target Language *</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={targetLanguage}
              onValueChange={setTargetLanguage}
              style={styles.picker}
            >
              {languages.map((lang) => (
                <Picker.Item key={lang.code} label={lang.label} value={lang.code} />
              ))}
            </Picker>
          </View>
          
          <PrimaryButton
            title={uploadError ? 'Retry Upload' : 'Upload Session'}
            onPress={handleUpload}
            loading={isUploading}
            style={styles.button}
          />

          {uploadError && (
            <View style={styles.inlineError}>
              <Text style={styles.inlineErrorTitle}>Upload failed</Text>
              <Text style={styles.inlineErrorText}>{uploadError}</Text>
            </View>
          )}
          
          <PrimaryButton
            title="Cancel"
            onPress={handleCancel}
            variant="secondary"
            style={styles.button}
          />
        </View>
      )}
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
  timerContainer: {
    alignItems: 'center',
    marginVertical: 40,
  },
  timerText: {
    fontSize: 48,
    fontWeight: '700',
    color: colors.text,
    fontVariant: ['tabular-nums'],
  },
  recordingIndicator: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
    marginTop: 8,
  },
  pausedIndicator: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF9500',
    marginTop: 8,
  },
  controlsContainer: {
    gap: 12,
    marginBottom: 32,
  },
  button: {
    marginBottom: 8,
  },
  formContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
  },
  inlineError: {
    backgroundColor: '#FFF5F5',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#F3C6C6',
    marginBottom: 12,
  },
  inlineErrorTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#D32F2F',
    marginBottom: 4,
  },
  inlineErrorText: {
    fontSize: 13,
    color: colors.mutedText,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  pickerContainer: {
    backgroundColor: colors.background,
    borderRadius: 8,
    marginBottom: 12,
  },
  picker: {
    // Platform-specific styling
  },
});

