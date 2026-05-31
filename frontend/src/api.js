import axios from 'axios'

const api = axios.create({
  // Берем адрес бэкенда из файла .env
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api