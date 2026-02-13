import { api } from './api'

// Machine Learning service - handles ML predictions and training
export const mlService = {
  // Get ML model info
  async getInfo() {
    const response = await api.get('/ml/info')
    return await response.json()
  },

  // Predict frame
  async predict(filename, frameIndex, withGradCAM = false) {
    const response = await api.post(`/ml/predict/${filename}/frame/${frameIndex}`, null, { with_gradcam: withGradCAM })
    return await response.json()
  },

  // Get GradCAM visualization URL
  getGradCAMUrl(filename, frameIndex, alpha = 0.5) {
    return `/ml/predict/${filename}/frame/${frameIndex}/gradcam?alpha=${alpha}`
  },

  // Start training
  async train(epochs = 20, batchSize = 16) {
    return await api.post('/ml/train', null, { epochs, batch_size: batchSize })
  },

  // Get training status
  async getTrainingStatus() {
    const response = await api.get('/ml/training-status')
    return await response.json()
  }
}
