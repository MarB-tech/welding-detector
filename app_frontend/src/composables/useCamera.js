import { ref, onMounted, onUnmounted } from 'vue'
import { cameraService } from '../services/cameraService'

// Camera control composable
export function useCamera(showToast) {
  const cameraRunning = ref(true)
  const streamUrl = ref(cameraService.getStreamUrl())
  const streamError = ref(false)
  const showSettings = ref(false)
  const cameraSettings = ref({
    contrast: 128,
    jpeg_quality: 90,
    fps: 30,
    resolution: 'HD'
  })
  const monochrome = ref(false)

  async function toggleCamera() {
    try {
      if (cameraRunning.value) {
        await cameraService.stop()
        cameraRunning.value = false
        showToast('Kamera wyłączona')
      } else {
        await cameraService.start()
        cameraRunning.value = true
        showToast('Kamera włączona')
      }
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function capture() {
    try {
      const response = await cameraService.capture(true)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `capture_${Date.now()}.jpg`
      a.click()
      URL.revokeObjectURL(url)
      
      showToast('Zdjęcie zapisane')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function fetchSettings() {
    try {
      const data = await cameraService.getSettings()
      if (data.contrast !== undefined) cameraSettings.value.contrast = Math.round(data.contrast)
      if (data.jpeg_quality !== undefined) cameraSettings.value.jpeg_quality = data.jpeg_quality
      if (data.fps !== undefined) cameraSettings.value.fps = Math.round(data.fps)
      if (data.resolution !== undefined) cameraSettings.value.resolution = data.resolution
    } catch (e) {
      console.error('Failed to fetch camera settings:', e)
    }
  }

  async function updateSetting(name, value) {
    try {
      const settings = { [name]: value }
      await cameraService.updateSettings(settings)
      showToast(`${name} = ${value}`)
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function toggleMonochrome() {
    try {
      const newValue = !monochrome.value
      await cameraService.setMonochrome(newValue)
      monochrome.value = newValue
      showToast(monochrome.value ? 'Tryb monochromatyczny' : 'Tryb kolorowy')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function fetchMonochrome() {
    try {
      monochrome.value = await cameraService.getMonochrome()
    } catch (e) {
      console.error('Failed to fetch monochrome:', e)
    }
  }

  async function checkStatus() {
    try {
      const data = await cameraService.isRunning()
      cameraRunning.value = data.running
    } catch (e) {
      console.error('Failed to check camera status:', e)
    }
  }

  onMounted(() => {
    fetchSettings()
    fetchMonochrome()
    checkStatus()
  })

  return {
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
  }
}
