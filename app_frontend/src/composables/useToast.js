import { ref } from 'vue'

// Toast notification composable
export function useToast() {
  const toast = ref({
    show: false,
    message: '',
    type: 'success'
  })

  function showToast(message, type = 'success') {
    toast.value = { show: true, message, type }
    setTimeout(() => {
      toast.value.show = false
    }, 3000)
  }

  return {
    toast,
    showToast
  }
}
