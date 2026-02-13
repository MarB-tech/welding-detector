<template>
  <div v-if="show" class="bg-white p-4 rounded shadow mb-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Ustawienia kamery</h2>
      <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700 text-2xl leading-none">×</button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <!-- Contrast -->
      <div class="space-y-2">
        <label class="font-medium">Kontrast</label>
        <input 
          type="range" 
          min="0" 
          max="255" 
          :value="settings.contrast"
          @change="$emit('update-setting', 'contrast', Number($event.target.value))"
          class="w-full"
        >
        <div class="text-xs text-gray-500 flex justify-between">
          <span>0</span>
          <span class="font-mono text-lg">{{ settings.contrast }}</span>
          <span>255</span>
        </div>
      </div>

      <!-- JPEG Quality -->
      <div class="space-y-2">
        <label class="font-medium">Jakość JPEG</label>
        <input 
          type="range" 
          min="50" 
          max="100" 
          :value="settings.jpeg_quality"
          @change="$emit('update-setting', 'jpeg_quality', Number($event.target.value))"
          class="w-full"
        >
        <div class="text-xs text-gray-500 flex justify-between">
          <span>50%</span>
          <span class="font-mono text-lg">{{ settings.jpeg_quality }}%</span>
          <span>100%</span>
        </div>
      </div>

      <!-- FPS -->
      <div class="space-y-2">
        <label class="font-medium">FPS</label>
        <select 
          :value="settings.fps"
          @change="$emit('update-setting', 'fps', Number($event.target.value))"
          class="w-full p-2 border rounded text-lg"
        >
          <option :value="15">15 fps</option>
          <option :value="30">30 fps</option>
          <option :value="60">60 fps</option>
        </select>
      </div>

      <!-- Resolution -->
      <div class="space-y-2">
        <label class="font-medium">Rozdzielczość</label>
        <select 
          :value="settings.resolution"
          @change="$emit('update-setting', 'resolution', $event.target.value)"
          class="w-full p-2 border rounded text-lg"
        >
          <option value="HD">HD (1280×720)</option>
          <option value="FHD">FHD (1920×1080)</option>
        </select>
      </div>

      <!-- Monochrome -->
      <div class="space-y-2">
        <label class="font-medium">Tryb obrazu</label>
        <button 
          @click="$emit('toggle-monochrome')" 
          class="w-full p-2 rounded text-lg font-medium transition"
          :class="monochrome ? 'bg-gray-800 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
        >
          {{ monochrome ? 'Monochromatyczne' : 'Kolorowe' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  settings: Object,
  monochrome: Boolean
})

defineEmits(['close', 'update-setting', 'toggle-monochrome'])
</script>
