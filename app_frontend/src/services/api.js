// Base API configuration
const API_BASE = '' // Empty because Vite proxy handles routing

// Helper to build query strings
function buildQueryString(params) {
  if (!params) return ''
  const query = new URLSearchParams(params).toString()
  return query ? `?${query}` : ''
}

// Generic fetch wrapper with error handling
async function apiFetch(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${url}`, options)
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

// API methods
export const api = {
  get: (url, params) => apiFetch(url + buildQueryString(params)),
  
  post: (url, data, params) => apiFetch(url + buildQueryString(params), {
    method: 'POST',
    headers: data ? { 'Content-Type': 'application/json' } : {},
    body: data ? JSON.stringify(data) : undefined
  }),
  
  put: (url, data, params) => apiFetch(url + buildQueryString(params), {
    method: 'PUT',
    headers: data ? { 'Content-Type': 'application/json' } : {},
    body: data ? JSON.stringify(data) : undefined
  }),
  
  delete: (url) => apiFetch(url, { method: 'DELETE' })
}
