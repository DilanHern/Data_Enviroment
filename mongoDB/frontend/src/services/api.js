import axios from 'axios'

const API_BASE_URL = 'http://localhost:3004/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Clientes API
export const clientesApi = {
  getAll: () => api.get('/clientes'),
  getById: (id) => api.get(`/clientes/${id}`),
  create: (data) => api.post('/clientes', data),
  update: (id, data) => api.patch(`/clientes/${id}`, data),
  delete: (id) => api.delete(`/clientes/${id}`),
}

// Productos API
export const productosApi = {
  getAll: () => api.get('/productos'),
  getById: (id) => api.get(`/productos/${id}`),
  create: (data) => api.post('/productos', data),
  update: (id, data) => api.patch(`/productos/${id}`, data),
  delete: (id) => api.delete(`/productos/${id}`),
}

// Ordenes API
export const ordenesApi = {
  getAll: () => api.get('/ordenes'),
  getById: (id) => api.get(`/ordenes/${id}`),
  create: (data) => api.post('/ordenes', data),
  update: (id, data) => api.patch(`/ordenes/${id}`, data),
  delete: (id) => api.delete(`/ordenes/${id}`),
}

export default api
