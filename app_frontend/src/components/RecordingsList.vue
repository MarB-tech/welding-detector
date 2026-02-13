<template>
  <div class="bg-white p-4 rounded shadow">
    <h2 class="text-xl font-semibold mb-2 text-gray-800">Recordings</h2>
    
    <div v-if="recordings.length === 0" class="text-gray-500 text-center py-4">
      Brak nagrań
    </div>
    
    <table v-else class="w-full">
      <thead>
        <tr class="text-left border-b">
          <th class="py-2">Plik</th>
          <th class="py-2">Rozmiar</th>
          <th class="py-2">Notatka</th>
          <th class="py-2 text-right">Akcje</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="rec in recordings" 
          :key="rec.filename"
          class="border-b last:border-0 hover:bg-gray-50"
        >
          <td class="py-2">
            <span class="font-medium text-gray-700">{{ rec.filename }}</span>
            <span 
              v-if="rec.filename.includes('_trimmed')" 
              class="text-xs ml-2 px-2 py-0.5 rounded bg-green-200 text-green-800"
            >
              Przycięte
            </span>
            <span 
              v-if="rec.filename.includes('_postprocess')" 
              class="text-xs ml-2 px-2 py-0.5 rounded bg-blue-200 text-blue-800"
            >
              Post-processing
            </span>
            <span 
              v-if="rec.analysis?.in_progress"
              class="text-xs ml-2 px-2 py-0.5 rounded bg-yellow-200 text-yellow-800 animate-pulse"
            >
              Analiza... {{ Math.round(rec.analysis.progress || 0) }}%
            </span>
          </td>
          
          <td class="py-2 text-gray-500 text-sm">{{ rec.size_mb }} MB</td>
          
          <td class="py-2">
            <input 
              type="text" 
              :value="rec.note || ''"
              @blur="$emit('save-note', rec.filename, $event.target.value)"
              @keyup.enter="$event.target.blur()"
              placeholder="Dodaj notatkę..."
              class="w-full px-2 py-1 text-sm border rounded hover:border-blue-400 focus:border-blue-500 focus:outline-none"
            >
          </td>
          
          <td class="py-2 text-right">
            <div class="flex gap-1 justify-end">
              <button 
                @click="$emit('view-recording', rec.filename)"
                class="px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium"
                title="Przeglądaj klatki"
              >
                View
              </button>
              <button 
                @click="$emit('trim-to-motion', rec.filename)"
                :disabled="trimStatus[rec.filename]"
                class="px-2 py-1 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-sm font-medium disabled:opacity-50"
                title="Przytnij do ruchu"
              >
                Trim
              </button>
              <button 
                @click="$emit('trim-to-postprocess', rec.filename)"
                :disabled="trimStatus[rec.filename]"
                class="px-2 py-1 bg-purple-500 hover:bg-purple-600 text-white rounded text-sm font-medium disabled:opacity-50"
                title="Tylko post-processing"
              >
                Process
              </button>
              <button 
                @click="$emit('apply-overlay', rec.filename)"
                class="px-2 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded text-sm font-medium"
                title="Nałóż timestamp"
              >
                Overlay
              </button>
              <button 
                @click="$emit('analyze-video', rec.filename)"
                :disabled="rec.analysis?.in_progress"
                class="px-2 py-1 bg-indigo-500 hover:bg-indigo-600 text-white rounded text-sm font-medium disabled:opacity-50"
                title="Analizuj wideo"
              >
                Analyze
              </button>
              <button 
                v-if="rec.analysis?.results"
                @click="$emit('view-analysis', rec.filename)"
                class="px-2 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm font-medium"
                title="Zobacz wyniki"
              >
                Results
              </button>
              <button 
                @click="$emit('download', rec.filename)"
                class="px-2 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded text-sm font-medium"
                title="Pobierz"
              >
                Download
              </button>
              <button 
                @click="$emit('delete', rec.filename)"
                class="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-medium"
                title="Usuń"
              >
                Delete
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  recordings: Array,
  trimStatus: Object
})

defineEmits([
  'view-recording', 
  'save-note', 
  'download', 
  'delete', 
  'trim-to-motion', 
  'trim-to-postprocess', 
  'apply-overlay',
  'analyze-video',
  'view-analysis'
])
</script>
