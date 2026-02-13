import { ref } from 'vue'
import { recordingService } from '../services/recordingService'
import { labelingService } from '../services/labelingService'

// Frame viewer composable
export function useFrameViewer(showToast) {
  const frameViewer = ref({
    show: false,
    filename: '',
    currentFrame: 0,
    totalFrames: 0,
    imageUrl: '',
    loading: false,
    filters: {
      preset: '',
      clahe: 0,
      sharpen: 0,
      gamma: 1.0,
      contrast: 1.0,
      denoise: 0,
      edges: false,
      heatmap: ''
    },
    currentLabel: null,
    currentDefectType: null,
    autoAdvance: true
  })

  async function openFrameViewer(filename, startFrame = 0) {
    frameViewer.value.filename = filename
    frameViewer.value.currentFrame = startFrame
    frameViewer.value.loading = true
    frameViewer.value.show = true
    frameViewer.value.currentLabel = null
    resetFilters()
    
    try {
      const info = await recordingService.getInfo(filename)
      frameViewer.value.totalFrames = info.frame_count
      updateFrameImage()
      await fetchCurrentLabel()
    } catch (e) {
      showToast(e.message, 'error')
      frameViewer.value.show = false
    }
  }

  function updateFrameImage() {
    frameViewer.value.loading = true
    
    const url = recordingService.getFrameUrl(
      frameViewer.value.filename,
      frameViewer.value.currentFrame,
      frameViewer.value.filters
    )
    
    frameViewer.value.imageUrl = url + (url.includes('?') ? '&' : '?') + '_t=' + Date.now()
    
    const img = new Image()
    img.onload = () => frameViewer.value.loading = false
    img.onerror = () => frameViewer.value.loading = false
    img.src = frameViewer.value.imageUrl
  }

  function resetFilters() {
    frameViewer.value.filters = {
      preset: '',
      clahe: 0,
      sharpen: 0,
      gamma: 1.0,
      contrast: 1.0,
      denoise: 0,
      edges: false,
      heatmap: ''
    }
    if (frameViewer.value.show) updateFrameImage()
  }

  function prevFrame() {
    if (frameViewer.value.currentFrame > 0) {
      frameViewer.value.currentFrame--
      updateFrameImage()
      fetchCurrentLabel()
    }
  }

  function nextFrame() {
    if (frameViewer.value.currentFrame < frameViewer.value.totalFrames - 1) {
      frameViewer.value.currentFrame++
      updateFrameImage()
      fetchCurrentLabel()
    }
  }

  function downloadCurrentFrame() {
    const a = document.createElement('a')
    a.href = frameViewer.value.imageUrl
    a.download = `${frameViewer.value.filename}_frame${frameViewer.value.currentFrame}.jpg`
    a.click()
  }

  async function fetchCurrentLabel() {
    try {
      const data = await labelingService.getLabel(
        frameViewer.value.filename,
        frameViewer.value.currentFrame
      )
      frameViewer.value.currentLabel = data.label
      frameViewer.value.currentDefectType = data.defect_type || null
    } catch {
      frameViewer.value.currentLabel = null
      frameViewer.value.currentDefectType = null
    }
  }

  return {
    frameViewer,
    openFrameViewer,
    updateFrameImage,
    resetFilters,
    prevFrame,
    nextFrame,
    downloadCurrentFrame,
    fetchCurrentLabel
  }
}
