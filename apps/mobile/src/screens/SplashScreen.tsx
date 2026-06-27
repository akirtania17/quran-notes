import React, { useEffect, useRef } from 'react';
import { View, Pressable, StyleSheet, Dimensions, Animated, Easing } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Svg, { Defs, LinearGradient, Stop } from 'react-native-svg';
import { RootStackParamList } from '../navigation/types';
import {
  AlhamdulillahPaths,
  ALHAMDULILLAH_VIEWBOX,
} from '../assets/calligraphy/AlhamdulillahPaths';

const SCREEN_WIDTH = Dimensions.get('window').width;

// Animation timings
const FILL_DURATION = 1800;
const POST_FILL_HOLD = 400; // Brief hold after fill before navigation
const TOTAL_DURATION = FILL_DURATION + POST_FILL_HOLD;

// Calligraphy dimensions (match the traced SVG aspect ratio)
const CALLIGRAPHY_WIDTH = Math.min(SCREEN_WIDTH * 0.78, 420);
const CALLIGRAPHY_HEIGHT =
  CALLIGRAPHY_WIDTH * (ALHAMDULILLAH_VIEWBOX.height / ALHAMDULILLAH_VIEWBOX.width);

type SplashScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Splash'>;

export default function SplashScreen() {
  const navigation = useNavigation<SplashScreenNavigationProp>();
  const hasNavigated = useRef(false);

  // Animated values using React Native Animated
  const fillWidth = useRef(new Animated.Value(0)).current;

  const navigateToHome = () => {
    if (!hasNavigated.current) {
      hasNavigated.current = true;
      navigation.replace('Home');
    }
  };

  useEffect(() => {
    // Gold fill animation - LEFT to RIGHT
    Animated.timing(fillWidth, {
      toValue: CALLIGRAPHY_WIDTH,
      duration: FILL_DURATION,
      easing: Easing.bezier(0.25, 0.1, 0.25, 1), // Smooth ease-out
      useNativeDriver: false, // width animation requires non-native driver
    }).start();

    // Navigate after animation completes
    const timeout = setTimeout(() => {
      navigateToHome();
    }, TOTAL_DURATION);

    return () => clearTimeout(timeout);
  }, []);

  const handleTapToSkip = () => {
    navigateToHome();
  };

  return (
    <Pressable style={styles.container} onPress={handleTapToSkip}>
      <View style={styles.calligraphyContainer}>
        {/* BASE LAYER: White calligraphy (invisible on white background) */}
        <View style={styles.baseLayer}>
          <Svg
            width={CALLIGRAPHY_WIDTH}
            height={CALLIGRAPHY_HEIGHT}
            viewBox={`0 0 ${ALHAMDULILLAH_VIEWBOX.width} ${ALHAMDULILLAH_VIEWBOX.height}`}
          >
            <AlhamdulillahPaths fill="#FFFFFF" />
          </Svg>
        </View>

        {/* GOLD LAYER: Metallic gold fill revealed LEFT → RIGHT */}
        <Animated.View
          style={[
            styles.goldFillLayer,
            {
              width: fillWidth,
              overflow: 'hidden',
            },
          ]}
        >
          <Svg
            width={CALLIGRAPHY_WIDTH}
            height={CALLIGRAPHY_HEIGHT}
            viewBox={`0 0 ${ALHAMDULILLAH_VIEWBOX.width} ${ALHAMDULILLAH_VIEWBOX.height}`}
          >
            <Defs>
              {/* Metallic gold gradient - inspired by reference image */}
              <LinearGradient id="metallicGold" x1="0%" y1="0%" x2="0%" y2="100%">
                <Stop offset="0%" stopColor="#F5D576" stopOpacity="1" />
                <Stop offset="25%" stopColor="#E8B84C" stopOpacity="1" />
                <Stop offset="50%" stopColor="#D4A03A" stopOpacity="1" />
                <Stop offset="75%" stopColor="#C88F2F" stopOpacity="1" />
                <Stop offset="100%" stopColor="#B8860B" stopOpacity="1" />
              </LinearGradient>
            </Defs>
            <AlhamdulillahPaths fill="url(#metallicGold)" />
          </Svg>
        </Animated.View>

      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  calligraphyContainer: {
    position: 'relative',
    width: CALLIGRAPHY_WIDTH,
    height: CALLIGRAPHY_HEIGHT,
    justifyContent: 'center',
    alignItems: 'flex-start', // Left-aligned for LTR fill
    overflow: 'hidden',
  },
  baseLayer: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: CALLIGRAPHY_WIDTH,
    height: CALLIGRAPHY_HEIGHT,
  },
  goldFillLayer: {
    position: 'absolute',
    left: 0,
    top: 0,
    height: CALLIGRAPHY_HEIGHT,
    // overflow: 'hidden' is set via animated style
  },
});
