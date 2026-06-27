// Format seconds to MM:SS or HH:MM:SS
export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '00:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Date/time formatting lives in utils/date.ts, but many screens import it from utils/format.ts.
// Re-export here to keep imports stable.
import { formatDate as _formatDate, formatDateTime as _formatDateTime } from './date';
// Avoid re-export indirection that can become `undefined` depending on bundler/module interop.
export const formatDate = _formatDate;
export const formatDateTime = _formatDateTime;

// Truncate text with ellipsis
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

