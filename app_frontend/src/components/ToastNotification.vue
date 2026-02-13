<template>
  <div 
    v-if="toast.show"
    class="fixed bottom-5 right-5 px-6 py-3 rounded-lg shadow-lg text-white transition-opacity z-50"
    :class="toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'"
  >
    {{ toast.message }}
  </div>
</template>

<script setup>
defineProps({
  toast: {
    type: Object,
    required: true
  }
})
</script>
