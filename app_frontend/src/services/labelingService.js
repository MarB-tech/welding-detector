import { api } from './api'

// Labeling service - handles frame labeling
export const labelingService = {
  // Save label for a frame
  async saveLabel(filename, frameIndex, label, defectType = null) {
    return await api.post(`/labeling/${filename}/frame/${frameIndex}`, {
      label,
      defect_type: defectType,
      save_image: true
    })
  },

  // Get label for a frame
  async getLabel(filename, frameIndex) {
    try {
      const response = await api.get(`/labeling/${filename}/frame/${frameIndex}`)
      return await response.json()
    } catch {
      return { label: null, defect_type: null }
    }
  },

  // Delete label
  async deleteLabel(filename, frameIndex) {
    return await api.delete(`/labeling/${filename}/frame/${frameIndex}`)
  },

  // Get labeling statistics
  async getStats() {
    const response = await api.get('/labeling/stats')
    return await response.json()
  }
}
