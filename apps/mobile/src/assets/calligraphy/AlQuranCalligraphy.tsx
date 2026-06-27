import React from 'react';
import Svg, { Path, G, Defs, LinearGradient, Stop } from 'react-native-svg';
import { ViewStyle } from 'react-native';

interface AlQuranCalligraphyProps {
  width?: number;
  height?: number;
  style?: ViewStyle;
  /**
   * Optional gradient ID override if you want to control fill externally.
   * If not provided, uses a default metallic gold gradient.
   */
  fillGradientId?: string;
}

/**
 * Arabic calligraphy for "القرآن" (Al-Quran)
 * 
 * This is a placeholder SVG with proper viewBox and centering.
 * Replace the Path d="..." values with traced calligraphy paths later
 * without needing to modify the animation code.
 * 
 * ViewBox: 0 0 400 200 (centered, scalable)
 */
export default function AlQuranCalligraphy({
  width = 300,
  height = 150,
  style,
  fillGradientId,
}: AlQuranCalligraphyProps) {
  const gradientId = fillGradientId || 'defaultGoldGradient';
  const fillUrl = `url(#${gradientId})`;

  return (
    <Svg
      width={width}
      height={height}
      viewBox="0 0 400 200"
      style={style}
    >
      {!fillGradientId && (
        <Defs>
          <LinearGradient id="defaultGoldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <Stop offset="0%" stopColor="#F5D576" stopOpacity="1" />
            <Stop offset="35%" stopColor="#E8B84C" stopOpacity="1" />
            <Stop offset="65%" stopColor="#D4A03A" stopOpacity="1" />
            <Stop offset="100%" stopColor="#C88F2F" stopOpacity="1" />
          </LinearGradient>
        </Defs>
      )}
      
      <G>
        {/* 
          Placeholder calligraphy paths for "القرآن"
          These are simplified elegant strokes representing Arabic calligraphy.
          Replace with actual traced SVG paths from final design.
        */}
        
        {/* Alif-Lam (ال) - right portion */}
        <Path
          d="M 320 80 Q 330 70, 340 80 L 340 140 Q 340 150, 330 150 L 310 150 Q 300 150, 300 140 L 300 90 Q 300 80, 310 80 Z"
          fill={fillUrl}
        />
        <Path
          d="M 355 75 L 365 75 Q 370 75, 370 80 L 370 145 Q 370 155, 360 155 Q 355 155, 355 150 L 355 80 Q 355 75, 355 75 Z"
          fill={fillUrl}
        />
        
        {/* Qaf (ق) - center-right */}
        <Path
          d="M 220 90 Q 245 70, 270 90 Q 280 100, 280 115 Q 280 135, 260 145 Q 240 155, 220 135 Q 210 125, 210 110 Q 210 95, 220 90 Z M 240 110 Q 240 120, 250 120 Q 260 120, 260 110 Q 260 100, 250 100 Q 240 100, 240 110 Z"
          fill={fillUrl}
        />
        <Path
          d="M 235 155 L 235 165 Q 235 168, 238 168 Q 241 168, 241 165 L 241 155"
          fill={fillUrl}
        />
        <Path
          d="M 250 155 L 250 168 Q 250 171, 253 171 Q 256 171, 256 168 L 256 155"
          fill={fillUrl}
        />
        
        {/* Ra (ر) - center */}
        <Path
          d="M 140 130 Q 170 115, 190 130 Q 195 135, 195 142 Q 195 152, 185 157 Q 170 162, 155 152 Q 145 145, 145 138 Q 145 130, 155 125 Z"
          fill={fillUrl}
        />
        
        {/* Alif (ا) - center-left */}
        <Path
          d="M 105 75 L 115 75 Q 120 75, 120 80 L 120 145 Q 120 155, 110 155 Q 105 155, 105 150 L 105 80 Q 105 75, 105 75 Z"
          fill={fillUrl}
        />
        
        {/* Noon (ن) - left portion */}
        <Path
          d="M 30 125 Q 45 110, 70 115 Q 85 118, 92 128 Q 95 135, 90 142 Q 80 152, 60 150 Q 40 147, 32 138 Q 28 132, 30 125 Z"
          fill={fillUrl}
        />
        <Path
          d="M 55 105 Q 55 102, 58 102 Q 61 102, 61 105 Q 61 108, 58 108 Q 55 108, 55 105 Z"
          fill={fillUrl}
        />
      </G>
    </Svg>
  );
}

