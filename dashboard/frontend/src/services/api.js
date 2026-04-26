import axios from 'axios'
import { getToken, resetToken, API_BASE } from './auth'

// Authenticated GET request
async function get(endpoint, params = {}) {
  try {
    const token = await getToken()
    const response = await axios.get(`${API_BASE}${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` },
      params,
      timeout: 120000
    })
    return response.data
  } catch (err) {
    if (err.response?.status === 401) {
      resetToken()
      const token = await getToken()
      const response = await axios.get(`${API_BASE}${endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
        timeout: 120000
      })
      return response.data
    }
    throw err
  }
}

// ── API calls ───────────────────────────────────────────────────────────────────

export const fetchPortfolioSummary = (periodYears = 1) =>
  get('/portfolio/summary', { period_years: periodYears })

export const fetchRiskMetrics = (periodYears = 1, universe = 'nifty50') =>
  get('/risk/metrics', { period_years: periodYears, universe })

export const fetchRiskSurface = (periodYears = 1) =>
  get('/risk/surface', { period_years: periodYears })

export const fetchCorrelationMatrix = (periodYears = 1) =>
  get('/portfolio/correlation', { period_years: periodYears })

export const fetchIndiaVix = () =>
  get('/market/vix')

export const fetchCircuitBreakers = () =>
  get('/market/circuits')

export const fetchExpiryPremium = () =>
  get('/market/expiry')

export const fetchStressTest = (scenario = 'all') =>
  get('/risk/stress', { scenario })

export const fetchAssets = () =>
  get('/assets/')

export const fetchBenchmarkComparison = (periodYears = 1) =>
  get('/portfolio/benchmark', { period_years: periodYears })

export const fetchMarketIndicators = () =>
  get('/assets/indices')

// Public endpoint — no auth needed
export async function fetchMarketPrices() {
    try {
        const response = await axios.get(
            `${API_BASE}/market/prices`,
            { timeout: 15000 }
        )
        return response.data
    } catch {
        return null
    }
}