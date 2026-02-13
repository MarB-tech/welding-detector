import { ref, onMounted, onUnmounted } from 'vue'
import { recordingService } from '../services/recordingService'

// Recording management composable
export function useRecordings(showToast) {
  const isRecording = ref(false)
  const recordingDuration = ref(0)
  const recordings = ref([])
  const overlayStatus = ref({})
  const trimStatus = ref({})
  const analysisPolling = ref(null)
  
  let statusInterval = null
  let overlayPollInterval = null

  async function startRecording() {
    try {
      await recordingService.startRecording()
      isRecording.value = true
      showToast('Nagrywanie rozpoczęte')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function stopRecording() {
    try {
      const data = await recordingService.stopRecording()
      isRecording.value = false
      recordingDuration.value = 0
      showToast(`Zapisano: ${data.filename} (${data.duration_seconds}s)`)
      await fetchRecordings()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function fetchRecordings() {
    try {
      recordings.value = await recordingService.getRecordings()
      restoreAnalysisResults()
    } catch (e) {
      console.error('Error fetching recordings:', e)
      showToast('Nie można pobrać listy nagrań', 'error')
    }
  }

  async function deleteRecording(filename) {
    if (!confirm(`Usunąć ${filename}?`)) return
    
    try {
      await recordingService.deleteRecording(filename)
      showToast('Usunięto')
      await fetchRecordings()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function saveNote(filename, note) {
    try {
      await recordingService.addNote(filename, note)
      const rec = recordings.value.find(r => r.filename === filename)
      if (rec) rec.note = note
    } catch (e) {
      showToast('Nie udało się zapisać notatki', 'error')
    }
  }

  function downloadRecording(filename) {
    window.open(recordingService.getDownloadUrl(filename))
  }

  async function trimToMotion(filename) {
    try {
      trimStatus.value[filename] = 'trimming'
      showToast('Przycinanie do ruchu rozpoczęte...')
      
      const data = await recordingService.trimToMotion(filename)
      
      if (data.status === 'no_motion') {
        showToast('Nie wykryto ruchu w nagraniu', 'error')
      } else {
        showToast(`Przycięto! ${data.output_filename} (${data.duration_seconds}s, -${data.reduction_percent}%)`)
        await fetchRecordings()
      }
      delete trimStatus.value[filename]
    } catch (e) {
      showToast(e.message, 'error')
      delete trimStatus.value[filename]
    }
  }

  async function trimToPostProcessing(filename) {
    try {
      trimStatus.value[filename] = 'postprocessing'
      showToast('Wycinanie procesu spawania...')
      
      const data = await recordingService.trimToPostprocess(filename)
      showToast(`Gotowe! ${data.output_filename} - tylko post-processing (${data.duration_seconds}s, -${data.reduction_percent}%)`)
      delete trimStatus.value[filename]
      await fetchRecordings()
    } catch (e) {
      showToast(e.message, 'error')
      delete trimStatus.value[filename]
    }
  }

  async function applyOverlay(filename) {
    try {
      await recordingService.applyOverlay(filename)
      overlayStatus.value[filename] = { status: 'processing', progress: 0 }
      showToast('Nakładanie overlay rozpoczęte')
      startOverlayPolling()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  async function startVideoAnalysis(filename) {
    try {
      await recordingService.analyzeVideo(filename, 5)
      showToast('Analiza wideo rozpoczęta')
      
      const recording = recordings.value.find(r => r.filename === filename)
      if (recording) {
        recording.analysis = { 
          in_progress: true, 
          progress: 0,
          results: null,
          error: null
        }
      }
      
      startAnalysisPolling()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  function startAnalysisPolling() {
    if (analysisPolling.value) return
    
    analysisPolling.value = setInterval(async () => {
      const analyzingRecordings = recordings.value.filter(r => r.analysis?.in_progress)
      
      if (analyzingRecordings.length === 0) {
        stopAnalysisPolling()
        return
      }
      
      for (const rec of analyzingRecordings) {
        try {
          const status = await recordingService.getAnalysisStatus(rec.filename)
          
          if (status.status === 'completed') {
            const results = await recordingService.getAnalysisResults(rec.filename)
            rec.analysis = { in_progress: false, results }
            saveAnalysisResults()
            showToast(`Analiza "${rec.filename}" zakończona`)
          } else if (status.status === 'in_progress') {
            if (!rec.analysis) rec.analysis = {}
            rec.analysis.in_progress = true
            rec.analysis.progress = status.progress || 0
          } else if (status.status === 'error') {
            rec.analysis = { error: status.error || 'Unknown error' }
            showToast(`Błąd analizy "${rec.filename}"`, 'error')
          }
        } catch (e) {
          console.error('Error polling analysis status:', e)
        }
      }
    }, 2000)
  }

  function stopAnalysisPolling() {
    if (analysisPolling.value) {
      clearInterval(analysisPolling.value)
      analysisPolling.value = null
    }
  }

  async function pollOverlayStatus() {
    try {
      const data = await recordingService.getOverlayJobs()
      
      for (const [filename, status] of Object.entries(data)) {
        overlayStatus.value[filename] = status
        if (status.status === 'completed') {
          await fetchRecordings()
        }
      }
      
      const hasActive = Object.values(data).some(s => s.status === 'processing')
      if (!hasActive && overlayPollInterval) {
        clearInterval(overlayPollInterval)
        overlayPollInterval = null
      }
    } catch (e) {
      console.error('Overlay status check failed:', e)
    }
  }

  function startOverlayPolling() {
    if (overlayPollInterval) return
    overlayPollInterval = setInterval(pollOverlayStatus, 2000)
  }

  async function pollRecordingStatus() {
    try {
      const data = await recordingService.getStatus()
      isRecording.value = data.is_recording
      recordingDuration.value = data.duration_seconds ? Math.floor(data.duration_seconds) : 0
    } catch (e) {
      console.error('Status check failed:', e)
    }
  }

  function saveAnalysisResults() {
    try {
      const analysisData = {}
      recordings.value.forEach(rec => {
        if (rec.analysis?.results) {
          analysisData[rec.filename] = rec.analysis
        }
      })
      localStorage.setItem('analysisResults', JSON.stringify(analysisData))
    } catch (e) {
      console.error('Error saving analysis results:', e)
    }
  }

  function restoreAnalysisResults() {
    try {
      const saved = localStorage.getItem('analysisResults')
      if (!saved) return
      
      const analysisData = JSON.parse(saved)
      recordings.value.forEach(rec => {
        if (analysisData[rec.filename]) {
          rec.analysis = analysisData[rec.filename]
        }
      })
    } catch (e) {
      console.error('Error restoring analysis results:', e)
    }
  }

  onMounted(() => {
    fetchRecordings()
    pollRecordingStatus()
    
    statusInterval = setInterval(() => {
      pollRecordingStatus()
    }, isRecording.value ? 2000 : 5000)
  })

  onUnmounted(() => {
    if (statusInterval) clearInterval(statusInterval)
    if (overlayPollInterval) clearInterval(overlayPollInterval)
    stopAnalysisPolling()
  })

  return {
    isRecording,
    recordingDuration,
    recordings,
    overlayStatus,
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
  }
}
