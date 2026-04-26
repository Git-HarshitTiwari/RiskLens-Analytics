import { TrendingUp, TrendingDown, Shield, Activity, BarChart2, Calendar } from 'lucide-react'

function StatCard({ title, value, subtitle, trend, icon: Icon, color }) {
  const colors = {
    green:  { bg: 'bg-green-950/30',  border: 'border-green-800/30',  text: 'text-green-400',  icon: 'bg-green-900/50'  },
    red:    { bg: 'bg-red-950/30',    border: 'border-red-800/30',    text: 'text-red-400',    icon: 'bg-red-900/50'    },
    orange: { bg: 'bg-orange-950/30', border: 'border-orange-800/30', text: 'text-orange-400', icon: 'bg-orange-900/50' },
    blue:   { bg: 'bg-blue-950/30',   border: 'border-blue-800/30',   text: 'text-blue-400',   icon: 'bg-blue-900/50'   },
    purple: { bg: 'bg-purple-950/30', border: 'border-purple-800/30', text: 'text-purple-400', icon: 'bg-purple-900/50' },
    gray:   { bg: 'bg-[#16161e]',     border: 'border-[#2a2a3e]',     text: 'text-gray-300',   icon: 'bg-[#2a2a3e]'    },
  }

  const c = colors[color] || colors.gray

  return (
    <div className={`${c.bg} border ${c.border} rounded-xl p-5 flex flex-col gap-4 
                     hover:border-opacity-60 transition-all duration-200`}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-widest font-medium">
          {title}
        </span>
        <div className={`${c.icon} p-1.5 rounded-lg`}>
          <Icon size={13} className={c.text} />
        </div>
      </div>
      <div>
        <div className={`text-2xl font-bold font-mono ${c.text} leading-none`}>
          {value}
        </div>
        <div className="text-xs text-gray-600 mt-1.5">{subtitle}</div>
      </div>
      {trend !== undefined && (
        <div className="flex items-center gap-1">
          {trend >= 0
            ? <TrendingUp size={11} className="text-green-500" />
            : <TrendingDown size={11} className="text-red-500" />
          }
          <span className={`text-xs font-mono ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {trend >= 0 ? '+' : ''}{trend?.toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  )
}

export default function SummaryCards({ data }) {
  if (!data) return null

  const totalReturn = data['total_return_%']      ?? data.total_return_pct   ?? 0
  const var95       = data['portfolio_var_95_%']   ?? data.portfolio_var_95   ?? 0
  const cvar95      = data['portfolio_cvar_95_%']  ?? data.portfolio_cvar_95  ?? 0
  const sharpe      = data['portfolio_sharpe']     ?? 0
  const numAssets   = data['num_assets']           ?? 0
  const dataStart   = data['data_start']           ?? '—'
  const dataEnd     = data['data_end']             ?? '—'

  const returnColor  = totalReturn >= 0 ? 'green' : 'red'
  const varColor     = var95 <= -3 ? 'red' : var95 <= -2 ? 'orange' : 'green'
  const sharpeColor  = sharpe >= 1.5 ? 'green' : sharpe >= 1 ? 'orange' : 'red'

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard
        title="Total Return"
        value={`${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`}
        subtitle="Equal-weighted portfolio"
        trend={totalReturn}
        icon={TrendingUp}
        color={returnColor}
      />
      <StatCard
        title="VaR 95%"
        value={`${var95.toFixed(3)}%`}
        subtitle="Daily max expected loss"
        icon={Shield}
        color={varColor}
      />
      <StatCard
        title="CVaR 95%"
        value={`${cvar95.toFixed(3)}%`}
        subtitle="Avg loss on worst days"
        icon={Shield}
        color="red"
      />
      <StatCard
        title="Sharpe Ratio"
        value={sharpe.toFixed(3)}
        subtitle="Risk-adjusted return"
        icon={Activity}
        color={sharpeColor}
      />
      <StatCard
        title="Assets"
        value={numAssets.toString()}
        subtitle="Nifty 50 stocks tracked"
        icon={BarChart2}
        color="blue"
      />
      <StatCard
        title="Data Range"
        value={dataEnd}
        subtitle={`From ${dataStart}`}
        icon={Calendar}
        color="purple"
      />
    </div>
  )
}