import { ref } from 'vue'
import { mlService } from '../services/mlService'

// Machine learning composable
export function useMachineLearning(showToast) {
  const mlInfo = ref(null)
  const mlPrediction = ref(null)
  const mlPredicting = ref(false)
  const trainingInProgress = ref(false)
  const showingGradCAM = ref(false)

  async function fetchMLInfo() {
    try {
      mlInfo.value = await mlService.getInfo()
    } catch (e) {
      console.error('Failed to fetch ML info:', e)
    }
  }

  async function predictFrame(filename, frameIndex) {
    mlPredicting.value = true
    mlPrediction.value = null
    
    try {
      mlPrediction.value = await mlService.predict(filename, frameIndex, false)
      const label = mlPrediction.value.prediction === 'ok' ? 'OK' : 'NOK'
      showToast(`${label}: ${mlPrediction.value.confidence}%`)
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      mlPredicting.value = false
    }
  }

  function showGradCAM(filename, frameIndex) {
    showingGradCAM.value = true
    const url = mlService.getGradCAMUrl(filename, frameIndex, 0.5)
    showToast('Pokazuję Grad-CAM - obszary uwagi AI')
    return url + `&_t=${Date.now()}`
  }

  async function startTraining() {
    trainingInProgress.value = true
    
    try {
      await mlService.train(20, 16)
      showToast('Trening rozpoczęty w tle!')
      
      const pollTraining = setInterval(async () => {
        const status = await mlService.getTrainingStatus()
        
        if (!status.in_progress) {
          clearInterval(pollTraining)
          trainingInProgress.value = false
          
          if (status.error) {
            showToast('Trening nieudany: ' + status.error, 'error')
          } else {
            showToast(`Trening zakończony! Dokładność: ${status.history?.best_val_acc?.toFixed(1)}%`)
            await fetchMLInfo()
          }
        }
      }, 3000)
    } catch (e) {
      showToast(e.message, 'error')
      trainingInProgress.value = false
    }
  }

  return {
    mlInfo,
    mlPrediction,
    mlPredicting,
    trainingInProgress,
    showingGradCAM,
    fetchMLInfo,
    predictFrame,
    showGradCAM,
    startTraining
  }
}
