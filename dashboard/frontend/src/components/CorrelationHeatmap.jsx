import Plot from 'react-plotly.js'
import LoadingSpinner, { ErrorCard } from './LoadingSpinner'

export default function CorrelationHeatmap({ data, loading, error }) {
  if (loading) return <LoadingSpinner message="Computing correlation matrix..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const tickers = data.tickers ?? []
  const matrix  = data.matrix  ?? []

  if (!tickers.length || !matrix.length) {
    return <ErrorCard message="No correlation data available." />
  }

  const labels = tickers.map(t => t.replace('.NS', ''))

  // Compute insight stats
  const upper = []
  for (let i = 0; i < matrix.length; i++)
    for (let j = i + 1; j < matrix[i].length; j++)
      upper.push(matrix[i][j])

  const avgCorr  = (upper.reduce((a, b) => a + b, 0) / upper.length).toFixed(3)
  const highCorr = upper.filter(v => v > 0.7).length
  const negCorr  = upper.filter(v => v < 0).length

  return (
    <div>
      <Plot
        data={[{
          type:          'heatmap',
          x:             labels,
          y:             labels,
          z:             matrix,
          colorscale: [
            [0.0,  '#1d4ed8'],
            [0.25, '#93c5fd'],
            [0.5,  '#f8fafc'],
            [0.75, '#fca5a5'],
            [1.0,  '#dc2626'],
          ],
          zmid:          0,
          zmin:         -1,
          zmax:          1,
          colorbar: {
            title:    { text: 'Correlation', font: { color: '#9ca3af', size: 11 } },
            tickfont: { color: '#9ca3af', size: 10 },
            tickvals: [-1, -0.5, 0, 0.5, 1],
            ticktext: ['-1.0', '-0.5', '0', '+0.5', '+1.0'],
            thickness: 12,
            len:       0.8,
          },
          hovertemplate: '<b>%{y} × %{x}</b><br>Correlation: %{z:.3f}<extra></extra>',
        }]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor:  'transparent',
          margin:        { l: 70, r: 20, t: 10, b: 80 },
          height:        460,
          xaxis: {
            tickfont:  { color: '#6b7280', size: 8 },
            tickangle: -45,
            gridcolor: '#1e1e2e',
          },
          yaxis: {
            tickfont:   { color: '#6b7280', size: 8 },
            gridcolor:  '#1e1e2e',
            autorange:  'reversed',
          },
        }}
        config={{
          displayModeBar: false,
          responsive:     true,
        }}
        style={{ width: '100%' }}
      />

      {/* Insight bar */}
      <div className="flex items-center gap-4 mt-2 pt-3 border-t border-[#1e1e2e]">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600">Avg correlation:</span>
          <span className="text-xs font-mono text-gray-300">{avgCorr}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600">High corr pairs (&gt;0.7):</span>
          <span className="text-xs font-mono text-orange-400">{highCorr}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600">Negative pairs:</span>
          <span className="text-xs font-mono text-blue-400">{negCorr}</span>
        </div>
      </div>
    </div>
  )
}