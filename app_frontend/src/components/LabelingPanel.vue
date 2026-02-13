<template>
  <div>
    <hr class="my-4">
    <h4 class="font-bold text-sm mb-3 text-gray-700">Etykietowanie</h4>
    
    <!-- Current label display -->
    <div v-if="currentLabel" class="mb-3 p-2 rounded text-center text-sm font-bold"
      :class="{
        'bg-green-200 text-green-600': currentLabel === 'ok',
        'bg-red-200 text-red-600': currentLabel === 'nok',
        'bg-gray-200 text-gray-600': currentLabel === 'skip'
      }">
      {{ currentLabel === 'ok' ? 'OK' : currentLabel === 'nok' ? 'NOK' : 'SKIP' }}
    </div>
    
    <!-- Label buttons -->
    <div class="grid grid-cols-3 gap-2 mb-3">
      <button 
        @click="$emit('label', 'ok')"
        class="px-2 py-2 bg-green-500 hover:bg-green-600 text-white rounded text-sm font-bold"
        :class="{ 'ring-4 ring-green-300': currentLabel === 'ok' }"
      >
        OK
      </button>
      <button 
        @click="showDefectSelector = true"
        class="px-2 py-2 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-bold"
        :class="{ 'ring-4 ring-red-300': currentLabel === 'nok' }"
      >
        NOK
      </button>
      <button 
        @click="$emit('label', 'skip')"
        class="px-2 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded text-sm font-bold"
        :class="{ 'ring-4 ring-gray-300': currentLabel === 'skip' }"
      >
        SKIP
      </button>
    </div>
    
    <!-- Defect type selector -->
    <div v-if="showDefectSelector" class="mb-3 p-3 bg-red-50 rounded border-2 border-red-200">
      <h5 class="font-bold text-sm mb-2 text-red-800">Wybierz typ wady:</h5>
      <div class="grid grid-cols-2 gap-1">
        <button 
          v-for="defect in defectTypes" 
          :key="defect.value"
          @click="$emit('label-with-defect', defect.value)"
          class="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs"
        >
          {{ defect.label }}
        </button>
      </div>
      <button 
        @click="showDefectSelector = false"
        class="w-full mt-2 px-2 py-1 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded text-xs"
      >
        Anuluj
      </button>
    </div>
    
    <!-- Current defect type -->
    <div v-if="currentDefectType && currentLabel === 'nok'" 
      class="mb-3 p-2 bg-red-100 rounded text-center text-sm">
      <span class="text-red-800">Typ wady: <strong>{{ getDefectLabel(currentDefectType) }}</strong></span>
    </div>
    
    <!-- Auto-advance -->
    <label class="flex items-center gap-2 text-sm mb-3">
      <input 
        type="checkbox" 
        :checked="autoAdvance"
        @change="$emit('update:autoAdvance', $event.target.checked)"
      >
      <span>Auto-przejdź do następnej</span>
    </label>
    
    <!-- Stats -->
    <div v-if="stats" class="text-xs text-gray-500 bg-white p-2 rounded">
      <div class="flex justify-between">
        <span>OK:</span>
        <strong>{{ stats.ok_count }}</strong>
      </div>
      <div class="flex justify-between">
        <span>NOK:</span>
        <strong>{{ stats.nok_count }}</strong>
      </div>
      <div v-if="hasDefectCounts" class="mt-2 pt-2 border-t">
        <div 
          v-for="(count, type) in stats.defect_counts" 
          :key="type"
          class="flex justify-between text-xs"
        >
          <span>{{ getDefectLabel(type) }}:</span>
          <strong>{{ count }}</strong>
        </div>
      </div>
      <div class="flex justify-between font-bold border-t mt-1 pt-1">
        <span>Razem:</span>
        <strong>{{ stats.ok_count + stats.nok_count }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DEFECT_TYPES } from '../utils/constants'

const props = defineProps({
  currentLabel: String,
  currentDefectType: String,
  autoAdvance: Boolean,
  stats: Object
})

defineEmits(['label', 'label-with-defect', 'update:autoAdvance'])

const showDefectSelector = ref(false)
const defectTypes = DEFECT_TYPES

const hasDefectCounts = computed(() => 
  props.stats?.defect_counts && Object.keys(props.stats.defect_counts).length > 0
)

function getDefectLabel(type) {
  const defect = DEFECT_TYPES.find(d => d.value === type)
  return defect ? defect.label : type
}
</script>
