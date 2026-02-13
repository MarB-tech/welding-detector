// Defect types with labels and icons
export const DEFECT_TYPES = [
  { value: 'porosity', label: 'Porowatość', icon: 'P' },
  { value: 'crack', label: 'Pęknięcie', icon: 'C' },
  { value: 'lack_of_fusion', label: 'Brak przetopu', icon: 'LF' },
  { value: 'undercut', label: 'Podtopienie', icon: 'U' },
  { value: 'burn_through', label: 'Przepalenie', icon: 'BT' },
  { value: 'spatter', label: 'Rozpryski', icon: 'S' },
  { value: 'irregular_bead', label: 'Nierówna spoina', icon: 'IB' },
  { value: 'contamination', label: 'Zanieczyszczenie', icon: 'CN' },
  { value: 'other', label: 'Inna wada', icon: '?' }
]

// Filter presets for image enhancement
export const FILTER_PRESETS = [
  { value: 'detail', label: 'Detail' },
  { value: 'bright', label: 'Bright' },
  { value: 'contrast', label: 'Contrast' },
  { value: 'edges', label: 'Edges' }
]

// Camera resolutions
export const CAMERA_RESOLUTIONS = [
  { value: 'HD', label: 'HD (1280×720)' },
  { value: 'FHD', label: 'FHD (1920×1080)' }
]

// Camera FPS options
export const CAMERA_FPS_OPTIONS = [15, 30, 60]
