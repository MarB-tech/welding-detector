<template>
  <div class="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
    <h3 class="font-bold text-lg mb-4">Filtry obrazu</h3>
    
    <!-- Preset -->
    <div class="mb-4">
      <label class="font-medium text-sm">Preset</label>
      <select 
        :value="filters.preset" 
        @change="$emit('update:filters', { ...filters, preset: $event.target.value })"
        class="w-full mt-1 p-2 border rounded"
      >
        <option value="">-- Brak --</option>
        <option value="detail">Detail</option>
        <option value="bright">Bright</option>
        <option value="contrast">Contrast</option>
        <option value="edges">Edges</option>
      </select>
    </div>
    
    <hr class="my-4">
    <h4 class="font-medium text-sm mb-3">Ręczne ustawienia</h4>
    
    <!-- CLAHE -->
    <div class="mb-3">
      <label class="text-sm flex justify-between">
        <span>CLAHE</span>
        <span class="font-mono">{{ filters.clahe }}</span>
      </label>
      <input 
        type="range" 
        min="0" 
        max="4" 
        step="0.5" 
        :value="filters.clahe"
        @input="$emit('update:filters', { ...filters, clahe: Number($event.target.value) })"
        class="w-full"
      >
    </div>
    
    <!-- Sharpen -->
    <div class="mb-3">
      <label class="text-sm flex justify-between">
        <span>Sharpen</span>
        <span class="font-mono">{{ filters.sharpen }}</span>
      </label>
      <input 
        type="range" 
        min="0" 
        max="3" 
        step="0.5" 
        :value="filters.sharpen"
        @input="$emit('update:filters', { ...filters, sharpen: Number($event.target.value) })"
        class="w-full"
      >
    </div>
    
    <!-- Gamma -->
    <div class="mb-3">
      <label class="text-sm flex justify-between">
        <span>Gamma</span>
        <span class="font-mono">{{ filters.gamma.toFixed(1) }}</span>
      </label>
      <input 
        type="range" 
        min="0.3" 
        max="3" 
        step="0.1" 
        :value="filters.gamma"
        @input="$emit('update:filters', { ...filters, gamma: Number($event.target.value) })"
        class="w-full"
      >
    </div>
    
    <!-- Contrast -->
    <div class="mb-3">
      <label class="text-sm flex justify-between">
        <span>Contrast</span>
        <span class="font-mono">{{ filters.contrast.toFixed(1) }}</span>
      </label>
      <input 
        type="range" 
        min="0.5" 
        max="3" 
        step="0.1" 
        :value="filters.contrast"
        @input="$emit('update:filters', { ...filters, contrast: Number($event.target.value) })"
        class="w-full"
      >
    </div>
    
    <!-- Denoise -->
    <div class="mb-3">
      <label class="text-sm flex justify-between">
        <span>Denoise</span>
        <span class="font-mono">{{ filters.denoise }}</span>
      </label>
      <input 
        type="range" 
        min="0" 
        max="15" 
        step="1" 
        :value="filters.denoise"
        @input="$emit('update:filters', { ...filters, denoise: Number($event.target.value) })"
        class="w-full"
      >
    </div>
    
    <!-- Edges -->
    <div class="mb-3">
      <label class="flex items-center gap-2 text-sm">
        <input 
          type="checkbox" 
          :checked="filters.edges"
          @change="$emit('update:filters', { ...filters, edges: $event.target.checked })"
        >
        <span>Detekcja krawędzi</span>
      </label>
    </div>
    
    <!-- Heatmap -->
    <div class="mb-3">
      <label class="text-sm">Heatmap</label>
      <select 
        :value="filters.heatmap"
        @change="$emit('update:filters', { ...filters, heatmap: $event.target.value })"
        class="w-full mt-1 p-2 border rounded text-sm"
      >
        <option value="">Brak</option>
        <option value="jet">Jet</option>
        <option value="hot">Hot</option>
        <option value="cool">Cool</option>
      </select>
    </div>
    
    <!-- Reset -->
    <button 
      @click="$emit('reset-filters')" 
      class="w-full mt-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm"
    >
      Reset filtrów
    </button>
    
    <!-- Download -->
    <button 
      @click="$emit('downoad-frame')" l
      class="w-full mt-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm"
    >
      Pobierz klatkę
    </button>
  </div>
</template>

<script setup>
defineProps({
  filters: Object
})

defineEmits(['update:filters', 'reset-filters', 'download-frame'])
</script>
