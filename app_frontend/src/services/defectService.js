import { api } from './api'

// Defect classification service - handles defect type predictions
export const defectService = {
  // Get defect classifier info
  async getInfo() {
    const response = await api.get('/defects/info')
    return await response.json()
  },

  // Predict defect type
  async predict(filename, frameIndex) {
    const response = await api.post('/defects/predict', null, { filename, frame_index: frameIndex })
    return await response.json()
  },

  // Get GradCAM for defect prediction
  getGradCAMUrl(filename, frameIndex) {
    return `/defects/predict/${filename}/frame/${frameIndex}/gradcam`
  },

  // Train defect classifier
  async train(epochs = 30, batchSize = 16) {
    return await api.post('/defects/train', null, { epochs, batch_size: batchSize })
  }
}
