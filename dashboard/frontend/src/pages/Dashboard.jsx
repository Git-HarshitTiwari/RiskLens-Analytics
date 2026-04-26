import { useState, useCallback } from 'react'
import Navbar             from '../components/Navbar'
import SummaryCards       from '../components/SummaryCards'
import VixPanel           from '../components/VixPanel'
import RiskSurface3D      from '../components/RiskSurface3D'
import CorrelationHeatmap from '../components/CorrelationHeatmap'
import CircuitTable       from '../components/CircuitTable'
import StockSelector      from '../components/StockSelector'
import LoadingSpinner, { ErrorCard } from '../components/LoadingSpinner'
import { useApi, useApiWithPeriod } from '../hooks/useApi'
import {
  fetchPortfolioSummary,
  fetchRiskSurface,
  fetchCorrelationMatrix,
  fetchIndiaVix,
  fetchCircuitBreakers,
  fetchRiskMetrics,
  fetchStressTest,
  fetchExpiryPremium,
} from '../services/api'
import Plot from 'react-plotly.js'

const SCENARIO_LABELS = {
  covid_crash:             'COVID Crash (Mar 2020)',
  global_financial_crisis: 'Global Financial Crisis 2008',
  inr_depreciation:        'INR Depreciation Shock',
  volatility_spike:        'Volatility Spike',
  fii_selloff:             'FII Mass Selloff',
}

const TABS = [
  { id: 'metrics', label: 'Risk Metrics' },
  { id: 'stress',  label: 'Stress Test'  },
  { id: 'expiry',  label: 'F&O Expiry'   },
]

export default function Dashboard() {
  const [period,      setPeriod]      = useState(1)
  const [selected,    setSelected]    = useState([])
  const [activeTab,   setActiveTab]   = useState('metrics')
  const [lastUpdated, setLastUpdated] = useState(null)

  const summary  = useApiWithPeriod(fetchPortfolioSummary,  period)
  const surface  = useApiWithPeriod(fetchRiskSurface,       period)
  const corr     = useApiWithPeriod(fetchCorrelationMatrix, period)
  const metrics  = useApiWithPeriod(fetchRiskMetrics,       period)
  const vix      = useApi(fetchIndiaVix,       [], true)
  const circuits = useApi(fetchCircuitBreakers,[], true)
  const stress   = useApi(fetchStressTest,     [], true)
  const expiry   = useApi(fetchExpiryPremium,  [], true)

  async function refreshAll() {
    await Promise.all([
      summary.refetch(period),
      surface.refetch(period),
      corr.refetch(period),
      metrics.refetch(period),
      vix.refetch(),
      circuits.refetch(),
      stress.refetch(),
      expiry.refetch(),
    ])
    setLastUpdated(new Date().toLocaleTimeString())
  }

  const metricsData     = metrics.data?.metrics ?? []
  const filteredMetrics = selected.length > 0
    ? metricsData.filter(m => selected.includes(m.ticker?.replace('.NS', '')))
    : metricsData

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Navbar
        period={period}
        onPeriodChange={setPeriod}
        onRefresh={refreshAll}
        lastUpdated={lastUpdated}
      />

      <main className="max-w-screen-2xl mx-auto px-8 py-10 flex flex-col gap-8">

        {/* Summary Cards */}
        {summary.loading
          ? <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i}
                     className="bg-[#16161e] border border-[#2a2a3e]
                                rounded-xl h-32 animate-pulse" />
              ))}
            </div>
          : summary.error
            ? <ErrorCard message={summary.error} />
            : <SummaryCards data={summary.data} />
        }

        {/* Stock Selector */}
        <StockSelector selected={selected} onChange={setSelected} />

        {/* VIX Panel */}
        <VixPanel
          data={vix.data}
          loading={vix.loading}
          error={vix.error}
        />

        {/* 3D Risk Surface */}
        <div className="bg-[#16161e] border border-[#2a2a3e] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">
                3D Rolling VaR Risk Surface
              </h2>
              <p className="text-xs text-gray-600 mt-0.5">
                Nifty 50 — 95% Value at Risk across stocks and time
              </p>
            </div>
            <span className="text-xs text-gray-600 bg-[#0f0f13]
                             border border-[#2a2a3e] rounded-lg px-3 py-1.5">
              Drag to rotate · Scroll to zoom
            </span>
          </div>
          <RiskSurface3D
            data={surface.data}
            loading={surface.loading}
            error={surface.error}
          />
        </div>

        {/* Correlation + Circuit Breakers */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 bg-[#16161e] border border-[#2a2a3e]
                          rounded-xl p-6">
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-white">
                Correlation Matrix
              </h2>
              <p className="text-xs text-gray-600 mt-0.5">
                Nifty 50 — pairwise return correlation
              </p>
            </div>
            <CorrelationHeatmap
              data={corr.data}
              loading={corr.loading}
              error={corr.error}
            />
          </div>

          <div className="lg:col-span-2 bg-[#16161e] border border-[#2a2a3e]
                          rounded-xl p-6">
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-white">
                Circuit Breaker Summary
              </h2>
              <p className="text-xs text-gray-600 mt-0.5">
                Stocks hitting NSE 10% price limits
              </p>
            </div>
            <CircuitTable
              data={circuits.data}
              loading={circuits.loading}
              error={circuits.error}
            />
          </div>
        </div>

        {/* Bottom Tabs */}
        <div className="bg-[#16161e] border border-[#2a2a3e] rounded-xl overflow-hidden">
          {/* Tab bar */}
          <div className="flex gap-0 border-b border-[#2a2a3e] bg-[#0f0f13] px-4 pt-2">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-2.5 text-sm font-medium transition-all border-b-2 mr-3 rounded-t-lg
                     ${activeTab === tab.id
                        ? 'border-blue-500 text-blue-400 bg-[#16161e]'
                        : 'border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#16161e]/50'
                     }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === 'metrics' && (
              <MetricsTable
                data={filteredMetrics}
                loading={metrics.loading}
                error={metrics.error}
              />
            )}
            {activeTab === 'stress' && (
              <StressTest
                data={stress.data}
                loading={stress.loading}
                error={stress.error}
              />
            )}
            {activeTab === 'expiry' && (
              <ExpiryPanel
                data={expiry.data}
                loading={expiry.loading}
                error={expiry.error}
              />
            )}
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] mt-8 py-6 px-8">
        <div className="max-w-screen-2xl mx-auto flex items-center
                        justify-between text-xs text-gray-700">
          <span>RiskLens Analytics v1.0.0</span>
          <span>Data via yfinance (NSE) · FastAPI + React</span>
          <span>For educational and portfolio demonstration purposes</span>
        </div>
      </footer>
    </div>
  )
}

// ── Risk Metrics Table ──────────────────────────────────────────────────────────
function MetricsTable({ data, loading, error }) {
  const [sortKey, setSortKey] = useState('sharpe')
  const [sortDir, setSortDir] = useState('desc')

  if (loading) return <LoadingSpinner message="Computing risk metrics..." />
  if (error)   return <ErrorCard message={error} />
  if (!data?.length) return (
    <p className="text-sm text-gray-600 py-4 text-center">No data available.</p>
  )

  const cols = [
    { key: 'ticker',           label: 'Stock'     },
    { key: 'var_95',           label: 'VaR 95%'   },
    { key: 'cvar_95',          label: 'CVaR 95%'  },
    { key: 'sharpe',           label: 'Sharpe'    },
    { key: 'sortino',          label: 'Sortino'   },
    { key: 'max_drawdown_%',   label: 'Max DD %'  },
    { key: 'annualized_vol_%', label: 'Ann Vol %' },
    { key: 'beta_vs_nifty',    label: 'Beta'      },
  ]

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey] ?? 0
    const bv = b[sortKey] ?? 0
    return sortDir === 'desc' ? bv - av : av - bv
  })

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const handleDownloadCSV = async () => {
    try {
        const { getToken } = await import('../services/auth')
        const token = await getToken()
        const response = await fetch('/export/csv/metrics', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        if (!response.ok) throw new Error('Download failed')
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'risklens_risk_metrics.csv'
        a.click()
        window.URL.revokeObjectURL(url)
    } catch (err) {
        console.error('CSV download failed:', err)
    }
  }

  const sharpeColor = v =>
    v >= 1.5 ? 'text-green-400' : v >= 1.0 ? 'text-yellow-400' : 'text-red-400'

  const betaColor = v =>
    v > 1.3 ? 'text-red-400' : v > 1.0 ? 'text-orange-400' : 'text-green-400'

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
            <h3 className="text-sm font-semibold text-white">
            Per-Stock Risk Metrics
            </h3>
            <p className="text-xs text-gray-600 mt-0.5">
            Click any column header to sort. Use the stock filter above to narrow down.
            </p>
        </div>
        <div className="flex items-center gap-3">
            <button
                onClick={handleDownloadCSV}
                className="flex items-center gap-1.5 text-xs text-blue-400
                            border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20
                            rounded-lg px-3 py-1.5 transition-all"
            >
                ↓ Download CSV
            </button>
            <span className="text-xs text-gray-600 bg-[#0f0f13] border border-[#2a2a3e]
                    rounded-lg px-3 py-1.5">
                {sorted.length} stocks
            </span>
        </div>
    </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#2a2a3e]">
              {cols.map(col => (
                <th key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="pb-3 pr-6 text-left text-gray-500 font-medium
                               uppercase tracking-wider cursor-pointer
                               hover:text-gray-300 transition-colors
                               select-none whitespace-nowrap text-xs">
                  {col.label}
                  {sortKey === col.key && (
                    <span className="ml-1 text-blue-400">
                      {sortDir === 'desc' ? '↓' : '↑'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={i}
                  className="border-b border-[#1a1a2e] hover:bg-[#1a1a2e]
                             transition-colors">
                <td className="py-3 pr-6 font-mono font-bold text-blue-400">
                  {row.ticker?.replace('.NS', '') ?? '—'}
                </td>
                <td className="py-3 pr-6 font-mono text-red-400">
                  {row.var_95?.toFixed(4) ?? '—'}
                </td>
                <td className="py-3 pr-6 font-mono text-red-500">
                  {row.cvar_95?.toFixed(4) ?? '—'}
                </td>
                <td className={`py-3 pr-6 font-mono font-semibold
                                ${sharpeColor(row.sharpe)}`}>
                  {row.sharpe?.toFixed(3) ?? '—'}
                </td>
                <td className="py-3 pr-6 font-mono text-gray-300">
                  {row.sortino?.toFixed(3) ?? '—'}
                </td>
                <td className="py-3 pr-6 font-mono text-orange-400">
                  {row['max_drawdown_%']?.toFixed(2) ?? '—'}%
                </td>
                <td className="py-3 pr-6 font-mono text-gray-300">
                  {row['annualized_vol_%']?.toFixed(2) ?? '—'}%
                </td>
                <td className={`py-3 font-mono ${betaColor(row.beta_vs_nifty)}`}>
                  {row.beta_vs_nifty?.toFixed(3) ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Stress Test ─────────────────────────────────────────────────────────────────
function StressTest({ data, loading, error }) {
  if (loading) return <LoadingSpinner message="Running stress scenarios..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const scenarios = data.scenarios ?? {}

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-white">
          Historical Stress Scenarios
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">
          Simulated portfolio impact under major market events.
          Applied to equal-weighted Nifty 50 portfolio.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
                      xl:grid-cols-5 gap-4">
        {Object.entries(scenarios).map(([key, result]) => {
          const cumulReturn = result['simulated_cumulative_return_%'] ?? 0
          const stressedVar = result['stressed_var_95_%']             ?? 0
          const normalVar   = result['normal_var_95_%']               ?? 0
          const varDeteri   = result['var_deterioration_%']           ?? 0
          const worstDay    = result['worst_single_day_%']            ?? 0
          const duration    = result['duration_days']                 ?? 0
          const description = result['description']                   ?? ''

          const color = cumulReturn < -40 ? '#ef4444'
                      : cumulReturn < -20 ? '#f97316'
                      : cumulReturn < -10 ? '#eab308'
                      : '#22c55e'

          return (
            <div key={key}
                 className="bg-[#0f0f13] border border-[#2a2a3e] rounded-xl p-5
                            hover:border-[#3a3a5e] transition-all flex flex-col gap-3">
              <div>
                <div className="text-xs font-semibold text-gray-400 uppercase
                                tracking-wider mb-1">
                  {SCENARIO_LABELS[key] ?? key}
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {description}
                </p>
              </div>

              <div>
                <div className="text-3xl font-bold font-mono"
                     style={{ color }}>
                  {cumulReturn >= 0 ? '+' : ''}{cumulReturn.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-600 mt-0.5">
                  Simulated cumulative return
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3
                              border-t border-[#1e1e2e]">
                <div>
                  <div className="text-xs text-gray-600 mb-0.5">
                    Stressed VaR
                  </div>
                  <div className="text-sm font-mono font-semibold text-red-400">
                    {stressedVar.toFixed(3)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-600 mb-0.5">
                    Normal VaR
                  </div>
                  <div className="text-sm font-mono text-gray-400">
                    {normalVar.toFixed(3)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-600 mb-0.5">
                    VaR Deterioration
                  </div>
                  <div className="text-sm font-mono font-semibold text-orange-400">
                    {varDeteri.toFixed(3)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-600 mb-0.5">
                    Worst Single Day
                  </div>
                  <div className="text-sm font-mono font-semibold"
                       style={{ color }}>
                    {worstDay.toFixed(2)}%
                  </div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-gray-600 mb-0.5">Duration</div>
                  <div className="text-sm font-mono text-blue-400">
                    {duration} days
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Expiry Panel ────────────────────────────────────────────────────────────────
function ExpiryPanel({ data, loading, error }) {
  if (loading) return <LoadingSpinner message="Fetching F&O expiry data..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const records = data.expiry_premium ?? []
  const sorted  = [...records].sort((a, b) =>
    (b['expiry_premium_%'] ?? 0) - (a['expiry_premium_%'] ?? 0)
  )

  const labels = sorted.map(r => r.ticker?.replace('.NS', '') ?? '—')
  const prems  = sorted.map(r => r['expiry_premium_%'] ?? 0)
  const colors = prems.map(v =>
    v > 10 ? '#ef4444' : v > 5 ? '#f97316' : '#22c55e'
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="text-sm font-semibold text-white">
          F&O Expiry Week Volatility Premium
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">
          Volatility during NSE expiry weeks (last Thursday of month)
          vs normal weeks. Positive = more volatile around expiry.
        </p>
      </div>

      <Plot
        data={[{
          type:          'bar',
          x:             labels,
          y:             prems,
          marker:        { color: colors },
          hovertemplate: '<b>%{x}</b><br>Premium: %{y:.2f}%<extra></extra>',
        }]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor:  'transparent',
          margin:        { l: 50, r: 10, t: 10, b: 90 },
          height:        300,
          xaxis: {
            tickfont:  { color: '#6b7280', size: 10 },
            tickangle: -45,
            gridcolor: '#1e1e2e',
          },
          yaxis: {
            title:         { text: 'Premium %',
                             font: { color: '#9ca3af', size: 11 } },
            tickfont:      { color: '#6b7280', size: 10 },
            gridcolor:     '#1e1e2e',
            zeroline:      true,
            zerolinecolor: '#2a2a3e',
          },
          showlegend: false,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />

      <div>
        <div className="text-xs font-semibold text-gray-500 uppercase
                        tracking-widest mb-3">
          Top Expiry-Sensitive Stocks
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {sorted.slice(0, 5).map((r, i) => (
            <div key={i}
                 className="bg-[#0f0f13] border border-[#2a2a3e]
                            rounded-xl p-4">
              <div className="text-sm font-mono font-bold text-blue-400 mb-2">
                {r.ticker?.replace('.NS', '')}
              </div>
              <div className={`text-xl font-mono font-bold ${
                r['expiry_premium_%'] > 10 ? 'text-red-400' :
                r['expiry_premium_%'] > 5  ? 'text-orange-400' :
                                             'text-green-400'
              }`}>
                +{r['expiry_premium_%']?.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-600 mt-1">expiry premium</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}