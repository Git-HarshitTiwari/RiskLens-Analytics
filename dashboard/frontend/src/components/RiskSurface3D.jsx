import Plot from 'react-plotly.js'
import LoadingSpinner, { ErrorCard } from './LoadingSpinner'

export default function RiskSurface3D({ data, loading, error }) {
  if (loading) return <LoadingSpinner message="Computing 3D risk surface..." />
  if (error)   return <ErrorCard message={error} />
  if (!data)   return null

  const dates   = data.dates   ?? []
  const tickers = data.tickers ?? []
  const values  = data.values  ?? []

  if (!dates.length || !tickers.length || !values.length) {
    return <ErrorCard message="No surface data available." />
  }

  // Thin out dates for performance
  const step      = Math.max(1, Math.floor(dates.length / 60))
  const datesThin = dates.filter((_, i) => i % step === 0)
  const zThin     = values
    .filter((_, i) => i % step === 0)
    .map(row => row.map(v => Math.abs(v) * 100))

  const labels = tickers.map(t => t.replace('.NS', ''))

  return (
    <Plot
      data={[{
        type:        'surface',
        x:           labels,
        y:           datesThin,
        z:           zThin,
        colorscale: [
          [0.0,  '#00ff88'],
          [0.25, '#88ff00'],
          [0.5,  '#ffdd00'],
          [0.75, '#ff8800'],
          [1.0,  '#ff0033'],
        ],
        colorbar: {
          title:     { text: 'VaR 95% (%)', font: { color: '#9ca3af', size: 11 } },
          tickfont:  { color: '#9ca3af', size: 10 },
          thickness: 12,
          len:       0.7,
        },
        hovertemplate: '<b>%{x}</b><br>Date: %{y}<br>VaR: %{z:.3f}%<extra></extra>',
        lighting: { ambient: 0.7, diffuse: 0.8, specular: 0.2 },
        contours: {
          z: { show: true, usecolormap: true, highlightcolor: '#ffffff', project: { z: false } }
        },
      }]}
      layout={{
        scene: {
          xaxis: {
            title:      { text: 'Stock', font: { color: '#9ca3af', size: 11 } },
            tickfont:   { color: '#6b7280', size: 9 },
            gridcolor:  '#1e1e2e',
            bgcolor:    '#0f0f13',
          },
          yaxis: {
            title:      { text: 'Date', font: { color: '#9ca3af', size: 11 } },
            tickfont:   { color: '#6b7280', size: 9 },
            gridcolor:  '#1e1e2e',
            bgcolor:    '#0f0f13',
          },
          zaxis: {
            title:      { text: 'VaR 95% (%)', font: { color: '#9ca3af', size: 11 } },
            tickfont:   { color: '#6b7280', size: 9 },
            gridcolor:  '#1e1e2e',
            bgcolor:    '#0f0f13',
          },
          bgcolor:  '#0f0f13',
          camera:   { eye: { x: 1.8, y: -1.8, z: 1.2 } },
        },
        paper_bgcolor: 'transparent',
        margin:        { l: 0, r: 0, t: 10, b: 0 },
        height:        500,
      }}
      config={{
        displayModeBar:          true,
        modeBarButtonsToRemove:  ['toImage'],
        displaylogo:             false,
        responsive:              true,
      }}
      style={{ width: '100%' }}
    />
  )
}