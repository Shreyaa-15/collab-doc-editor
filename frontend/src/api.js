import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const listDocuments  = ()           => api.get('/documents')
export const createDocument = (data)       => api.post('/documents', data)
export const getDocument    = (docId)      => api.get(`/documents/${docId}`)
export const getHistory     = (docId, rev) => api.get(`/documents/${docId}/history?since=${rev}`)