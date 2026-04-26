import { useState, useEffect, useCallback } from 'react'

// Generic hook for any API call
// Handles loading, error, and data states automatically
export function useApi(apiFn, deps = [], immediate = true) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError]     = useState(null)

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiFn(...args)
      setData(result)
      return result
    } catch (err) {
      setError(err.message || 'API call failed')
      return null
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => {
    if (immediate) execute()
  }, [execute])

  return { data, loading, error, refetch: execute }
}

// Hook with period parameter — refetches when period changes
export function useApiWithPeriod(apiFn, period) {
  return useApi(
    useCallback(() => apiFn(period), [period]),
    [period],
    true
  )
}