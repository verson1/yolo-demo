import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 0 })

http.interceptors.response.use(
  response => response.data,
  error => Promise.reject(new Error(
    error.response?.data?.error || (error.response?.status >= 500
      ? '后端服务暂不可用，请检查 Flask 和 MySQL 是否已启动。'
      : error.message || '请求失败'),
  )),
)

export const api = {
  model: () => http.get('/model/info'),
  summary: () => http.get('/dashboard/summary'),
  classes: () => http.get('/dashboard/classes'),
  trend: () => http.get('/dashboard/trend'),
  records: params => http.get('/records', { params }),
  record: id => http.get(`/records/${id}`),
  deleteRecord: id => http.delete(`/records/${id}`),
  detect: (type, file, confidence) => {
    const form = new FormData()
    form.append('file', file)
    form.append('confidence', confidence)
    return http.post(`/detect/${type}`, form)
  },
}
