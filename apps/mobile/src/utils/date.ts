// Get today's date in YYYY-MM-DD format
export function getTodayString(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Check if dateString is yesterday
export function isYesterday(dateString: string): boolean {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  const year = yesterday.getFullYear();
  const month = String(yesterday.getMonth() + 1).padStart(2, '0');
  const day = String(yesterday.getDate()).padStart(2, '0');
  const yesterdayStr = `${year}-${month}-${day}`;
  
  return dateString === yesterdayStr;
}

// Format ISO timestamp to readable format
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString();
}

// Format ISO timestamp to date only
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString();
}

