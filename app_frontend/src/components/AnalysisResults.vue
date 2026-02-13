<template>
  <div 
    v-if="show" 
    class="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex justify-between items-center p-4 border-b bg-gray-50">
        <h2 class="text-xl font-bold">Wyniki analizy: {{ filename }}</h2>
        <button @click="$emit('close')" class="text-gray-600 hover:text-gray-800 text-2xl leading-none">×</button>
      </div>

      <!-- Content -->
      <div v-if="results" class="p-6 overflow-y-auto flex-1">
        <!-- Summary -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-3">Podsumowanie</h3>
          <div class="grid grid-cols-2 gap-4">
            <div 
              :class="isNokPercentageHigh ? 'bg-red-100 border-red-300' : 'bg-green-100 border-green-300'"
              class="border rounded-lg p-4"
            >
              <div 
                :class="isNokPercentageHigh ? 'text-red-700' : 'text-green-700'"
                class="text-3xl font-bold"
              >
                {{ results.summary.ok + results.summary.nok }}
              </div>
              <div 
                :class="isNokPercentageHigh ? 'text-red-600' : 'text-green-600'"
                class="text-sm"
              >
                Przeanalizowanych klatek
              </div>
            </div>
            <div class="bg-red-100 border border-red-300 rounded-lg p-4">
              <div class="text-3xl font-bold text-red-700">{{ results.summary.nok }}</div>
              <div class="text-sm text-red-600">Klatki NOK</div>
            </div>
          </div>
        </div>

        <!-- Defect Summary -->
        <div v-if="hasDefects" class="mb-6">
          <h3 class="text-lg font-semibold mb-3">Wykryte wady</h3>
          <div class="grid grid-cols-2 gap-3">
            <div 
              v-for="(count, defectType) in results.defect_summary" 
              :key="defectType"
              class="bg-orange-100 border border-orange-300 rounded-lg p-3 flex items-center justify-between"
            >
              <span class="font-medium">{{ defectType }}</span>
              <span class="text-xl font-bold text-orange-700">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- NOK Frames List -->
        <div>
          <h3 class="text-lg font-semibold mb-3">
            Szczegóły klatek NOK ({{ nokFrames.length }})
          </h3>
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div 
              v-for="frame in nokFrames" 
              :key="frame.frame_number"
              class="bg-gray-50 border rounded p-3 hover:bg-gray-100 cursor-pointer"
              @click="$emit('view-frame', frame.frame_number)"
            >
              <div class="flex justify-between items-center">
                <span class="font-medium">Klatka {{ frame.frame_number }}</span>
                <span class="text-sm text-gray-500">{{ frame.confidence }}% pewności</span>
              </div>
              <div v-if="frame.defect_type" class="text-sm text-red-600 mt-1">
                {{ frame.defect_type }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t p-4 bg-gray-50 flex justify-end">
        <button 
          @click="$emit('close')"
          class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
        >
          Zamknij
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: Boolean,
  filename: String,
  results: Object
})

defineEmits(['close', 'view-frame'])

const nokFrames = computed(() => 
  props.results?.frames?.filter(f => f.prediction === 'nok') || []
)

const hasDefects = computed(() => 
  props.results?.defect_summary && Object.keys(props.results.defect_summary).length > 0
)

const isNokPercentageHigh = computed(() => {
  if (!props.results?.summary) return false
  const { ok, nok } = props.results.summary
  const total = ok + nok
  return total > 0 && (nok / total) > 0.1
})
</script>
