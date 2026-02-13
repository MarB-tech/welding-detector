import { api } from './api'

// Recording service - handles all recording-related API calls
export const recordingService = {
  // Start recording
  async startRecording() {
    return await api.post('/recording/start')
  },

  // Stop recording
  async stopRecording() {
    const response = await api.post('/recording/stop')
    return await response.json()
  },

  // Get recording status
  async getStatus() {
    const response = await api.get('/recording/status')
    return await response.json()
  },

  // Get list of recordings
  async getRecordings() {
    const response = await api.get('/recording/list')
    const data = await response.json()
    return data.recordings || []
  },

  // Delete recording
  async deleteRecording(filename) {
    return await api.delete(`/recording/${filename}`)
  },

  // Add/update note
  async addNote(filename, note) {
    return await api.put(`/recording/${filename}/note`, null, { note })
  },

  // Get download URL
  getDownloadUrl(filename) {
    return `/recording/download/${filename}`
  },

  // Get recording info
  async getInfo(filename) {
    const response = await api.get(`/recording/${filename}/info`)
    return await response.json()
  },

  // Get frame from recording
  getFrameUrl(filename, frameNumber, filters = {}) {
    const params = new URLSearchParams()
    
    if (filters.preset) params.append('preset', filters.preset)
    if (filters.clahe > 0) params.append('clahe', filters.clahe)
    if (filters.sharpen > 0) params.append('sharpen', filters.sharpen)
    if (filters.gamma !== 1.0) params.append('gamma', filters.gamma)
    if (filters.contrast !== 1.0) params.append('contrast', filters.contrast)
    if (filters.denoise > 0) params.append('denoise', filters.denoise)
    if (filters.edges) params.append('edges', 'true')
    if (filters.heatmap) params.append('heatmap', filters.heatmap)
    
    const query = params.toString()
    return `/recording/${filename}/frame/${frameNumber}${query ? '?' + query : ''}`
  },

  // Trim to motion
  async trimToMotion(filename) {
    const response = await api.post(`/recording/${filename}/trim-to-motion`, {})
    return await response.json()
  },

  // Trim to post-processing
  async trimToPostprocess(filename) {
    const response = await api.post(`/recording/${filename}/trim-to-postprocessing`)
    return await response.json()
  },

  // Apply overlay
  async applyOverlay(filename) {
    return await api.post(`/recording/${filename}/apply-overlay`)
  },

  // Get overlay jobs status
  async getOverlayJobs() {
    const response = await api.get('/recording/overlay-jobs')
    return await response.json()
  },

  // Analyze video
  async analyzeVideo(filename, skipFrames = 5) {
    return await api.post(`/ml/analyze-video/${filename}`, { skip_frames: skipFrames })
  },

  // Get analysis status
  async getAnalysisStatus(filename) {
    const response = await api.get(`/ml/analyze-video/${filename}/status`)
    return await response.json()
  },

  // Get analysis results
  async getAnalysisResults(filename) {
    const response = await api.get(`/ml/analyze-video/${filename}/results`)
    return await response.json()
  }
}
