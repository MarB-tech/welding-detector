<template>
  <div class="flex flex-wrap gap-3 mb-4">
    <button 
      @click="$emit('toggle-camera')" 
      :class="cameraRunning ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-500 hover:bg-green-600'"
      class="text-white px-4 py-2 rounded transition"
    >
      {{ cameraRunning ? 'Wyłącz kamerę' : 'Włącz kamerę' }}
    </button>
    
    <button 
      @click="$emit('capture')" 
      :disabled="!cameraRunning"
      class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Capture
    </button>
    
    <button 
      @click="$emit('start-recording')" 
      :disabled="isRecording || !cameraRunning"
      class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Start REC
    </button>
    
    <button 
      @click="$emit('stop-recording')" 
      :disabled="!isRecording"
      class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Stop
    </button>
    
    <button 
      @click="$emit('refresh')" 
      class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
    >
      Refresh
    </button>
    
    <button 
      @click="$emit('toggle-settings')" 
      class="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition"
    >
    Ustawienia
    </button>
  </div>
</template>

<script setup>
defineProps({
  cameraRunning: Boolean,
  isRecording: Boolean
})

defineEmits(['toggle-camera', 'capture', 'start-recording', 'stop-recording', 'refresh', 'toggle-settings'])
</script>
