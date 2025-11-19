import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:3000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const clientesApi = {
  getAll: () => api.get('/clientes'),
  getById: (id) => api.get(`/clientes/${id}`),
  create: (data) => api.post('/clientes', data),
  update: (id, data) => api.patch(`/clientes/${id}`, data),
  delete: (id) => api.delete(`/clientes/${id}`),
  search: (queryString) => api.get(`/clientes/search${queryString}`) // ✅ AGREGAR ESTA LÍNEA
}

export const productosApi = {
  getAll: () => api.get('/productos'),
  getById: (id) => api.get(`/productos/${id}`),
  create: (data) => api.post('/productos', data),
  update: (id, data) => api.patch(`/productos/${id}`, data),
  delete: (id) => api.delete(`/productos/${id}`)
}

export const ordenesApi = {
  getAll: () => api.get('/ordenes'),
  getById: (id) => api.get(`/ordenes/${id}`),
  create: (data) => api.post('/ordenes', data),
  update: (id, data) => api.patch(`/ordenes/${id}`, data),
  delete: (id) => api.delete(`/ordenes/${id}`)
}

export default api