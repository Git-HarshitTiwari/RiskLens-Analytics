import { useState } from 'react'
import { AlertTriangle, ArrowUp, ArrowDown, ChevronUp, ChevronDown } from 'lucide-react'
import LoadingSpinner, { ErrorCard } from './LoadingSpinner'

export default function CircuitTable({ data, loading, error }) {
  const [sortKey, setSortKey]   = useState('circuit_hits_total')
  const [sortDir, setSortDir]   = useState('desc')
  const [page, setPage]         = useState(0)
  const PAGE_SIZE = 10

  if (loading) return <LoadingSpinner message="Fetching circuit data..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const records = data.circuit_breakers ?? []

  const sorted = [...records].sort((a, b) => {
    const av = a[sortKey] ?? a[sortKey.charAt(0).toUpperCase() + sortKey.slice(1)] ?? 0
    const bv = b[sortKey] ?? b[sortKey.charAt(0).toUpperCase() + sortKey.slice(1)] ?? 0
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const paged      = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  function SortIcon({ col }) {
    if (sortKey !== col) return <ChevronUp size={10} className="text-gray-700" />
    return sortDir === 'desc'
      ? <ChevronDown size={10} className="text-blue-400" />
      : <ChevronUp   size={10} className="text-blue-400" />
  }

  function hitColor(hits) {
    if (hits >= 10) return 'text-red-400'
    if (hits >= 5)  return 'text-orange-400'
    if (hits >= 1)  return 'text-yellow-400'
    return 'text-gray-600'
  }

  const cols = [
    { key: 'ticker',             label: 'Stock'     },
    { key: 'circuit_hits_total', label: 'Total Hits' },
    { key: 'upper_circuits',     label: 'Upper ↑'   },
    { key: 'lower_circuits',     label: 'Lower ↓'   },
    { key: 'circuit_hit_rate_%', label: 'Hit Rate %' },
  ]

  return (
    <div className="flex flex-col h-full">
      <p className="text-xs text-gray-600 mb-3 leading-relaxed">
        Stocks hitting NSE 10% circuit limits. High frequency = elevated 
        volatility risk.
      </p>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#2a2a3e]">
              {cols.map(col => (
                <th key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="pb-2 pr-4 text-left text-gray-500 font-medium 
                               uppercase tracking-wider cursor-pointer 
                               hover:text-gray-300 transition-colors select-none">
                  <div className="flex items-center gap-1">
                    {col.label}
                    <SortIcon col={col.key} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, i) => {
              const ticker = (row.Ticker ?? row.ticker ?? row.stock ?? '').replace('.NS', '') || '—'
              const hits   = row.circuit_hits_total ?? 0
              const upper  = row.upper_circuits     ?? 0
              const lower  = row.lower_circuits     ?? 0
              const rate   = row['circuit_hit_rate_%'] ?? 0

              return (
                <tr key={i}
                    className="border-b border-[#1e1e2e] hover:bg-[#1a1a2e] transition-colors">
                  <td className="py-2.5 pr-4 font-mono font-semibold text-blue-400">
                    {ticker}
                  </td>
                  <td className={`py-2.5 pr-4 font-mono font-bold ${hitColor(hits)}`}>
                    {hits > 0 && <AlertTriangle size={10} className="inline mr-1 mb-0.5" />}
                    {hits}
                  </td>
                  <td className="py-2.5 pr-4 font-mono">
                    {upper > 0
                      ? <span className="text-green-400 flex items-center gap-1">
                          <ArrowUp size={10} />{upper}
                        </span>
                      : <span className="text-gray-700">0</span>
                    }
                  </td>
                  <td className="py-2.5 pr-4 font-mono">
                    {lower > 0
                      ? <span className="text-red-400 flex items-center gap-1">
                          <ArrowDown size={10} />{lower}
                        </span>
                      : <span className="text-gray-700">0</span>
                    }
                  </td>
                  <td className={`py-2.5 font-mono ${hitColor(rate)}`}>
                    {rate.toFixed(2)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3 pt-3 
                        border-t border-[#2a2a3e]">
          <span className="text-xs text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2.5 py-1 bg-[#1a1a2e] border border-[#2a2a3e] 
                         rounded text-xs text-gray-400 disabled:opacity-30 
                         hover:text-white transition-colors"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="px-2.5 py-1 bg-[#1a1a2e] border border-[#2a2a3e] 
                         rounded text-xs text-gray-400 disabled:opacity-30 
                         hover:text-white transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}