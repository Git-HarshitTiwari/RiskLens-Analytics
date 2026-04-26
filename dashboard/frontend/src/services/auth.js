import axios from 'axios'

const API_BASE = import.meta.env.DEV ? 'http://127.0.0.1:8000' : ''

// Module-level token cache
let _token = null

export async function getToken() {
  if (_token) return _token

  const response = await axios.post(`${API_BASE}/auth/login`, {
    username: 'admin',
    password: 'quantrisk123'
  })

  _token = response.data.access_token
  return _token
}

export function resetToken() {
  _token = null
}

export { API_BASE }