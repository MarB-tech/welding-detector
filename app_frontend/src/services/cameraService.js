import { api } from './api'

// Camera service - handles all camera-related API calls
export const cameraService = {
  // Start camera
  async start() {
    return await api.post('/camera/start')
  },

  // Stop camera
  async stop() {
    return await api.post('/camera/stop')
  },

  // Check if camera is running
  async isRunning() {
    const response = await api.get('/camera/running')
    return await response.json()
  },

  // Capture frame
  async capture(withOverlay = true) {
    return await api.get('/camera/capture', { overlay: withOverlay })
  },

  // Get camera settings
  async getSettings() {
    const response = await api.get('/camera/settings')
    return await response.json()
  },

  // Update camera settings
  async updateSettings(settings) {
    return await api.put('/camera/settings', settings)
  },

  // Toggle monochrome mode
  async setMonochrome(enabled) {
    await api.post('/camera/monochrome', null, { enabled })
    return enabled
  },

  // Get monochrome status
  async getMonochrome() {
    const response = await api.get('/camera/monochrome')
    const data = await response.json()
    return data.monochrome
  },

  // Get stream URL
  getStreamUrl() {
    return '/camera/stream'
  }
}
