<template>
  <div 
    v-if="show" 
    class="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-lg shadow-2xl w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex justify-between items-center p-4 border-b bg-gray-50">
        <h2 class="text-xl font-bold">
          {{ filename }} - Klatka {{ currentFrame }}/{{ totalFrames - 1 }}
        </h2>
        <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700 text-2xl leading-none">×</button>
      </div>
      
      <!-- Content -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Image -->
        <div class="flex-1 bg-gray-900 flex items-center justify-center p-4 relative">
          <img 
            :src="imageUrl" 
            class="max-w-full max-h-full object-contain"
            :class="{ 'opacity-50': loading }"
          >
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
            <div class="text-white text-xl font-semibold">Loading...</div>
          </div>
        </div>
        
        <!-- Sidebar -->
        <div class="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
          <slot name="sidebar"></slot>
        </div>
      </div>
      
      <!-- Footer - Navigation -->
      <div class="p-4 border-t bg-gray-50 flex items-center justify-between">
        <button 
          @click="$emit('prev-frame')" 
          :disabled="currentFrame <= 0"
          class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded disabled:opacity-50 font-medium"
        >
          ← Poprzednia
        </button>
        
        <div class="flex items-center gap-2">
          <input 
            type="range" 
            :min="0" 
            :max="totalFrames - 1" 
            :value="currentFrame"
            @input="$emit('update:currentFrame', Number($event.target.value))"
            class="w-64"
          >
          <input 
            type="number" 
            :value="currentFrame"
            @input="$emit('update:currentFrame', Number($event.target.value))"
            :min="0" 
            :max="totalFrames - 1"
            class="w-20 p-1 border rounded text-center"
          >
        </div>
        
        <button 
          @click="$emit('next-frame')" 
          :disabled="currentFrame >= totalFrames - 1"
          class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded disabled:opacity-50 font-medium"
        >
          Następna →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  filename: String,
  currentFrame: Number,
  totalFrames: Number,
  imageUrl: String,
  loading: Boolean
})

defineEmits(['close', 'prev-frame', 'next-frame', 'update:currentFrame'])
</script>
