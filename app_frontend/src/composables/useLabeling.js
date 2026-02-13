import { ref } from 'vue'
import { labelingService } from '../services/labelingService'

// Labeling composable
export function useLabeling(showToast, frameViewer) {
  const labelingStats = ref(null)
  const showDefectSelector = ref(false)

  async function labelFrame(label) {
    const filename = frameViewer.value.filename
    const frameIndex = frameViewer.value.currentFrame
    
    try {
      await labelingService.saveLabel(filename, frameIndex, label, null)
      frameViewer.value.currentLabel = label
      frameViewer.value.currentDefectType = null
      await fetchLabelingStats()
      
      if (frameViewer.value.autoAdvance && frameViewer.value.currentFrame < frameViewer.value.totalFrames - 1) {
        frameViewer.value.currentFrame++
        await fetchCurrentLabel()
      }
      
      showToast(`Klatka ${frameIndex} → ${label.toUpperCase()}`)
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function labelFrameWithDefect(defectType) {
    const filename = frameViewer.value.filename
    const frameIndex = frameViewer.value.currentFrame
    
    try {
      await labelingService.saveLabel(filename, frameIndex, 'nok', defectType)
      frameViewer.value.currentLabel = 'nok'
      frameViewer.value.currentDefectType = defectType
      showDefectSelector.value = false
      await fetchLabelingStats()
      
      if (frameViewer.value.autoAdvance && frameViewer.value.currentFrame < frameViewer.value.totalFrames - 1) {
        frameViewer.value.currentFrame++
        await fetchCurrentLabel()
      }
      
      showToast(`NOK - ${defectType}`)
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function removeLabel() {
    const filename = frameViewer.value.filename
    const frameIndex = frameViewer.value.currentFrame
    
    try {
      await labelingService.deleteLabel(filename, frameIndex)
      frameViewer.value.currentLabel = null
      await fetchLabelingStats()
      showToast('Etykieta usunięta')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function fetchLabelingStats() {
    try {
      labelingStats.value = await labelingService.getStats()
    } catch (e) {
      console.error('Failed to fetch labeling stats:', e)
    }
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
    labelingStats,
    showDefectSelector,
    labelFrame,
    labelFrameWithDefect,
    removeLabel,
    fetchLabelingStats,
    fetchCurrentLabel
  }
}
