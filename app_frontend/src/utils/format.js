// Format seconds as MM:SS
export function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// Format file size in MB
export function formatFileSize(bytes) {
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// Format timestamp for filenames
export function formatTimestamp(date = new Date()) {
  return date.toISOString().replace(/[:.]/g, '-').slice(0, -5)
}
