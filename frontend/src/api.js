const BASE_URL = import.meta.env.VITE_API_URL

const api = {
  async request(method, url, data = null, extraHeaders = {}) {
    const token = localStorage.getItem('token')

    const headers = {
      ...extraHeaders,
    }

    if (!(data instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${BASE_URL}${url}`, {
      method,
      headers,
      body: data instanceof FormData ? data : data ? JSON.stringify(data) : null,
    })

    // Обработка 401
    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/'
      return
    }

    if (!response.ok) {
      const error = new Error('HTTP error')
      error.response = {
        status: response.status,
        data: await response.json().catch(() => ({})),
      }
      throw error
    }

    return { data: await response.json() }
  },

  get(url) {
    return this.request('GET', url)
  },

  post(url, data, options = {}) {
    return this.request('POST', url, data)
  },
}

export default api