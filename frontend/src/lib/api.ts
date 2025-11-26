import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth API
export const authAPI = {
  signup: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/api/auth/signup', data),
  login: (data: { username: string; password: string }) =>
    api.post('/api/auth/login', data),
  getMe: () => api.get('/api/auth/me'),
}

// Credentials API
export const credentialsAPI = {
  create: (data: { credential_name: string; access_key: string; secret_key: string }) =>
    api.post('/api/credentials/', data),
  list: () => api.get('/api/credentials/'),
  get: (id: string) => api.get(`/api/credentials/${id}`),
  delete: (id: string) => api.delete(`/api/credentials/${id}`),
}

// Scan API
export const scanAPI = {
  create: (data: { scan_name: string; credential_id: string; regions?: string[] }) =>
    api.post('/api/scan/', data),
  list: () => api.get('/api/scan/'),
  get: (id: string) => api.get(`/api/scan/${id}`),
  delete: (id: string) => api.delete(`/api/scan/${id}`),
}

// Report API
export const reportAPI = {
  downloadPDF: (scanId: string) =>
    api.get(`/api/report/${scanId}/pdf`, { responseType: 'blob' }),
  downloadExcel: (scanId: string) =>
    api.get(`/api/report/${scanId}/excel`, { responseType: 'blob' }),
}

// S3 API
export const s3API = {
  uploadDocument: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/s3/upload-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listDocuments: () => api.get('/api/s3/documents'),
  deleteDocument: (fileName: string) => api.delete(`/api/s3/documents/${fileName}`),
}
