/**
 * Funções de acesso à API, agrupadas por recurso.
 *
 * Concentrar as URLs aqui evita strings mágicas espalhadas pelos componentes
 * e deixa qualquer mudança de contrato com um único ponto de edição.
 */
import api from './api'

// ------------------------------------------------------------------ auth
export const authService = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => api.post('/auth/login', payload).then((r) => r.data),
  logout: (refresh_token) => api.post('/auth/logout', { refresh_token }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  updateProfile: (payload) => api.patch('/auth/me', payload).then((r) => r.data),
  changePassword: (payload) => api.post('/auth/change-password', payload).then((r) => r.data),
}

// -------------------------------------------------------------- subjects
export const subjectService = {
  list: () => api.get('/subjects').then((r) => r.data),
  get: (id) => api.get(`/subjects/${id}`).then((r) => r.data),
  create: (payload) => api.post('/subjects', payload).then((r) => r.data),
  update: (id, payload) => api.patch(`/subjects/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/subjects/${id}`).then((r) => r.data),
}

// ----------------------------------------------------------------- notes
export const noteService = {
  list: (params) => api.get('/notes', { params }).then((r) => r.data),
  get: (id) => api.get(`/notes/${id}`).then((r) => r.data),
  create: (payload) => api.post('/notes', payload).then((r) => r.data),
  update: (id, payload) => api.patch(`/notes/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/notes/${id}`).then((r) => r.data),
  categories: () => api.get('/notes/categories').then((r) => r.data),
}

// ------------------------------------------------------------------ tags
export const tagService = {
  list: () => api.get('/tags').then((r) => r.data),
  remove: (id) => api.delete(`/tags/${id}`).then((r) => r.data),
}

// ------------------------------------------------------------- schedules
export const scheduleService = {
  list: (params) => api.get('/schedules', { params }).then((r) => r.data),
  upcoming: (params) => api.get('/schedules/upcoming', { params }).then((r) => r.data),
  get: (id) => api.get(`/schedules/${id}`).then((r) => r.data),
  create: (payload) => api.post('/schedules', payload).then((r) => r.data),
  update: (id, payload) => api.patch(`/schedules/${id}`, payload).then((r) => r.data),
  setStatus: (id, status) => api.patch(`/schedules/${id}/status`, { status }).then((r) => r.data),
  /** `scope`: 'this' (padrão) | 'following' | 'all' — relevante só para séries recorrentes. */
  remove: (id, scope) =>
    api.delete(`/schedules/${id}`, { params: scope ? { scope } : undefined }).then((r) => r.data),
  /** Baixa a agenda em .ics (blob, para download direto no navegador). */
  exportIcs: () => api.get('/schedules/export', { responseType: 'blob' }).then((r) => r.data),
  /** Gera (ou recupera) o token usado na URL pública de assinatura da agenda. */
  getExportToken: () => api.post('/schedules/export-token').then((r) => r.data),
}

// ---------------------------------------------------------------- search
export const searchService = {
  /** Busca links de apoio na web. `refresh` ignora o cache do servidor. */
  run: (payload, refresh = false) =>
    api.post('/search', payload, { params: { refresh }, timeout: 45000 }).then((r) => r.data),
  save: (payload) => api.post('/search/save', payload).then((r) => r.data),
  saved: (params) => api.get('/search/saved', { params }).then((r) => r.data),
  remove: (id) => api.delete(`/search/saved/${id}`).then((r) => r.data),
}

// --------------------------------------------------------- notifications
export const notificationService = {
  list: (params) => api.get('/notifications', { params }).then((r) => r.data),
  markRead: (id) => api.post(`/notifications/${id}/read`).then((r) => r.data),
  markAllRead: () => api.post('/notifications/read-all').then((r) => r.data),
  clearRead: () => api.delete('/notifications').then((r) => r.data),
}

// ------------------------------------------------------------- dashboard
export const dashboardService = {
  get: () => api.get('/dashboard').then((r) => r.data),
}
