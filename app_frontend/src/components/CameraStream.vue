<template>
  <div class="bg-black mb-4 rounded shadow flex items-center justify-center overflow-hidden relative" style="height: 70vh;">
    <img 
      :src="streamUrl" 
      class="object-contain w-full h-full"
      alt="Live stream"
      @error="$emit('error', true)"
      @load="$emit('error', false)"
    />
    <span v-if="hasError" class="text-gray-500 absolute">Brak połączenia z kamerą</span>
  </div>
</template>

<script setup>
defineProps({
  streamUrl: {
    type: String,
    required: true
  },
  hasError: {
    type: Boolean,
    default: false
  }
})

defineEmits(['error'])
</script>
