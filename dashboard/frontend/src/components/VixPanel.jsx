import Plot from 'react-plotly.js'
import LoadingSpinner, { ErrorCard } from './LoadingSpinner'

const REGIME_CONFIG = {
  'Calm':         { color: '#22c55e', bg: 'bg-green-950/40',  border: 'border-green-700/40'  },
  'Normal':       { color: '#3b82f6', bg: 'bg-blue-950/40',   border: 'border-blue-700/40'   },
  'Elevated':     { color: '#f97316', bg: 'bg-orange-950/40', border: 'border-orange-700/40' },
  'High Fear':    { color: '#ef4444', bg: 'bg-red-950/40',    border: 'border-red-700/40'    },
  'Extreme Fear': { color: '#dc2626', bg: 'bg-red-950/60',    border: 'border-red-600/60'    },
  'Unknown':      { color: '#6b7280', bg: 'bg-gray-900/40',   border: 'border-gray-700/40'   },
}

const REGIME_DESC = {
  'Calm':         'VIX < 15 — Market is relaxed',
  'Normal':       'VIX 15–20 — Typical conditions',
  'Elevated':     'VIX 20–25 — Caution advised',
  'High Fear':    'VIX 25–30 — Significant stress',
  'Extreme Fear': 'VIX > 30 — Crisis territory',
  'Unknown':      'Data unavailable',
}

export default function VixPanel({ data, loading, error }) {
  if (loading) return <LoadingSpinner message="Fetching India VIX..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const currentVix    = data.current_vix    ?? 0
  const currentRegime = data.current_regime ?? 'Unknown'
  const vixHistory    = data.vix_history    ?? {}

  const cfg     = REGIME_CONFIG[currentRegime] || REGIME_CONFIG['Unknown']
  const dates   = Object.keys(vixHistory)
  const values  = Object.values(vixHistory)

  return (
    <div className="bg-[#16161e] border border-[#2a2a3e] rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          India VIX — Market Fear Index
        </h2>
        <span className="text-xs text-gray-600">30-day history</span>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        {/* Left — Current reading */}
        <div className={`${cfg.bg} border ${cfg.border} rounded-xl p-4 
                         flex flex-col gap-2 md:w-48 shrink-0`}>
          <span className="text-xs text-gray-500 uppercase tracking-widest">
            Current VIX
          </span>
          <div className="text-4xl font-bold font-mono" style={{ color: cfg.color }}>
            {currentVix.toFixed(2)}
          </div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full w-fit"
               style={{ backgroundColor: `${cfg.color}20`, border: `1px solid ${cfg.color}40` }}>
            <div className="w-1.5 h-1.5 rounded-full animate-pulse"
                 style={{ backgroundColor: cfg.color }} />
            <span className="text-xs font-semibold" style={{ color: cfg.color }}>
              {currentRegime}
            </span>
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {REGIME_DESC[currentRegime]}
          </p>
        </div>

        {/* Right — Chart */}
        <div className="flex-1 min-w-0">
          <Plot
            data={[
              {
                x: dates,
                y: values,
                type: 'scatter',
                mode: 'lines',
                line: { color: cfg.color, width: 2 },
                fill: 'tozeroy',
                fillcolor: `${cfg.color}15`,
                hovertemplate: '<b>%{x}</b><br>VIX: %{y:.2f}<extra></extra>',
              }
            ]}
            layout={{
              paper_bgcolor: 'transparent',
              plot_bgcolor:  'transparent',
              margin: { l: 40, r: 10, t: 10, b: 40 },
              height: 160,
              xaxis: {
                tickfont:  { color: '#4b5563', size: 10 },
                gridcolor: '#1e1e2e',
                tickangle: -30,
              },
              yaxis: {
                tickfont:  { color: '#4b5563', size: 10 },
                gridcolor: '#1e1e2e',
              },
              shapes: [
                { type: 'line', x0: dates[0], x1: dates.at(-1), y0: 15, y1: 15,
                  line: { color: '#22c55e', width: 1, dash: 'dot' } },
                { type: 'line', x0: dates[0], x1: dates.at(-1), y0: 20, y1: 20,
                  line: { color: '#f97316', width: 1, dash: 'dot' } },
                { type: 'line', x0: dates[0], x1: dates.at(-1), y0: 25, y1: 25,
                  line: { color: '#ef4444', width: 1, dash: 'dot' } },
              ],
              showlegend: false,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </div>
  )
}