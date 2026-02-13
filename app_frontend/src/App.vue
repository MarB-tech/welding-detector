<template>
  <div class="min-h-screen bg-gray-100 p-4 font-sans">
    <!-- Header -->
    <header class="flex justify-between items-center mb-4 p-4 bg-white rounded shadow">
      <h1 class="text-2xl font-bold text-gray-800">Welding Detector</h1>
      <div class="flex items-center gap-2">
        <span v-if="isRecording" class="text-red-500 font-mono font-bold flex items-center gap-1">
          <span class="inline-block w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
          REC {{ formatDuration(recordingDuration) }}
        </span>
        <span v-else class="text-green-600 flex items-center gap-1">
          <span class="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
          Online
        </span>
      </div>
    </header>

    <!-- Camera Stream -->
    <CameraStream 
      :stream-url="streamUrl" 
      :has-error="streamError"
      @error="streamError = $event"
    />

    <!-- Control Panel -->
    <ControlPanel
      :camera-running="cameraRunning"
      :is-recording="isRecording"
      @toggle-camera="toggleCamera"
      @capture="capture"
      @start-recording="startRecording"
      @stop-recording="stopRecording"
      @refresh="fetchRecordings"
      @toggle-settings="showSettings = !showSettings"
    />

    <!-- Camera Settings -->
    <CameraSettings
      :show="showSettings"
      :settings="cameraSettings"
      :monochrome="monochrome"
      @close="showSettings = false"
      @update-setting="updateSetting"
      @toggle-monochrome="toggleMonochrome"
    />

    <!-- Toast Notification -->
    <ToastNotification :toast="toast" />

    <!-- Recordings List -->
    <RecordingsList
      :recordings="recordings"
      :trim-status="trimStatus"
      @view-recording="openFrameViewer"
      @save-note="saveNote"
      @download="downloadRecording"
      @delete="deleteRecording"
      @trim-to-motion="trimToMotion"
      @trim-to-postprocess="trimToPostProcessing"
      @apply-overlay="applyOverlay"
      @analyze-video="startVideoAnalysis"
      @view-analysis="viewAnalysis"
    />

    <!-- Frame Viewer Modal -->
    <FrameViewer
      :show="frameViewer.show"
      :filename="frameViewer.filename"
      :current-frame="frameViewer.currentFrame"
      :total-frames="frameViewer.totalFrames"
      :image-url="frameViewer.imageUrl"
      :loading="frameViewer.loading"
      @close="frameViewer.show = false"
      @prev-frame="prevFrame"
      @next-frame="nextFrame"
      @update:current-frame="onFrameChange"
    >
      <template #sidebar>
        <FilterSidebar
          :filters="frameViewer.filters"
          @update:filters="updateFilters"
          @reset-filters="resetFilters"
          @download-frame="downloadCurrentFrame"
        />
        <LabelingPanel
          :current-label="frameViewer.currentLabel"
          :current-defect-type="frameViewer.currentDefectType"
          :auto-advance="frameViewer.autoAdvance"
          :stats="labelingStats"
          @label="labelFrame"
          @label-with-defect="labelFrameWithDefect"
          @update:auto-advance="frameViewer.autoAdvance = $event"
        />
      </template>
    </FrameViewer>

    <!-- Analysis Results Modal -->
    <AnalysisResults
      :show="analysisModal.show"
      :filename="analysisModal.filename"
      :results="analysisModal.results"
      @close="analysisModal.show = false"
      @view-frame="openFrameFromAnalysis"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { formatDuration } from './utils/format'

// Components
import ToastNotification from './components/ToastNotification.vue'
import CameraStream from './components/CameraStream.vue'
import ControlPanel from './components/ControlPanel.vue'
import CameraSettings from './components/CameraSettings.vue'
import RecordingsList from './components/RecordingsList.vue'
import FrameViewer from './components/FrameViewer.vue'
import FilterSidebar from './components/FilterSidebar.vue'
import LabelingPanel from './components/LabelingPanel.vue'
import AnalysisResults from './components/AnalysisResults.vue'

// Composables
import { useToast } from './composables/useToast'
import { useCamera } from './composables/useCamera'
import { useRecordings } from './composables/useRecordings'
import { useFrameViewer } from './composables/useFrameViewer'
import { useLabeling } from './composables/useLabeling'

// Initialize composables
const { toast, showToast } = useToast()

const {
  cameraRunning,
  streamUrl,
  streamError,
  showSettings,
  cameraSettings,
  monochrome,
  toggleCamera,
  capture,
  updateSetting,
  toggleMonochrome
} = useCamera(showToast)

const {
  isRecording,
  recordingDuration,
  recordings,
  trimStatus,
  startRecording,
  stopRecording,
  fetchRecordings,
  deleteRecording,
  saveNote,
  downloadRecording,
  trimToMotion,
  trimToPostProcessing,
  applyOverlay,
  startVideoAnalysis
} = useRecordings(showToast)

const {
  frameViewer,
  openFrameViewer,
  updateFrameImage,
  resetFilters,
  prevFrame,
  nextFrame,
  downloadCurrentFrame
} = useFrameViewer(showToast)

const {
  labelingStats,
  labelFrame,
  labelFrameWithDefect,
  fetchLabelingStats
} = useLabeling(showToast, frameViewer)

// Analysis modal state
const analysisModal = ref({
  show: false,
  filename: '',
  results: null
})

// Watch for filter changes to update image
watch(() => frameViewer.value.filters, () => {
  if (frameViewer.value.show) {
    updateFrameImage()
  }
}, { deep: true })

// Watch for frame changes
watch(() => frameViewer.value.currentFrame, () => {
  if (frameViewer.value.show) {
    updateFrameImage()
  }
})

// Fetch labeling stats when frame viewer opens
watch(() => frameViewer.value.show, (show) => {
  if (show) {
    fetchLabelingStats()
  }
})

function updateFilters(newFilters) {
  frameViewer.value.filters = newFilters
}

function onFrameChange(frameNumber) {
  frameViewer.value.currentFrame = frameNumber
}

function viewAnalysis(filename) {
  const recording = recordings.value.find(r => r.filename === filename)
  if (!recording?.analysis?.results) {
    showToast('Brak wyników analizy', 'error')
    return
  }
  
  analysisModal.value = {
    show: true,
    filename,
    results: recording.analysis.results
  }
}

function openFrameFromAnalysis(frameNumber) {
  analysisModal.value.show = false
  openFrameViewer(analysisModal.value.filename, frameNumber)
}
</script>
