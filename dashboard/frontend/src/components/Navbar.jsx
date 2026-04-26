import { useState, useEffect, useCallback } from 'react'
import { TrendingUp, TrendingDown, RefreshCw, Clock, Wifi } from 'lucide-react'
import { fetchMarketPrices, fetchIndiaVix } from '../services/api'

// ── Market status config ──────────────────────────────────────────────────────
const STATUS_CONFIG = {
    'Open':       { color: '#22c55e', bg: 'bg-green-950/60',  border: 'border-green-800/40'  },
    'Closed':     { color: '#ef4444', bg: 'bg-red-950/60',    border: 'border-red-800/40'    },
    'Pre-Market': { color: '#f97316', bg: 'bg-orange-950/60', border: 'border-orange-800/40' },
    'Weekend':    { color: '#6b7280', bg: 'bg-gray-900/60',   border: 'border-gray-700/40'   },
}

// ── Single price ticker component ────────────────────────────────────────────
function PriceTicker({ label, data, prefix = '', decimals = 2 }) {
    if (!data) {
        return (
            <div className="flex flex-col items-center px-5
                            border-r border-[#1e1e2e] last:border-0">
                <span className="text-gray-600 text-xs uppercase
                                 tracking-widest mb-1">{label}</span>
                <span className="font-mono text-sm text-gray-700
                                 animate-pulse">—</span>
            </div>
        )
    }

    const isPositive = data.change_pct >= 0
    const changeColor = isPositive ? '#22c55e' : '#ef4444'

    return (
        <div className="flex flex-col items-center px-4
                        border-r border-[#1e1e2e] last:border-0 min-w-0">
            <span className="text-gray-600 text-xs uppercase
                             tracking-widest mb-0.5 whitespace-nowrap">
                {label}
            </span>
            <div className="flex items-baseline gap-1.5">
                <span className="font-mono font-bold text-sm text-gray-100">
                    {prefix}{data.price.toLocaleString('en-IN', {
                        maximumFractionDigits: decimals
                    })}
                </span>
                <span className="font-mono text-xs font-medium
                                 flex items-center gap-0.5"
                      style={{ color: changeColor }}>
                    {isPositive
                        ? <TrendingUp size={9} />
                        : <TrendingDown size={9} />
                    }
                    {isPositive ? '+' : ''}{data.change_pct.toFixed(2)}%
                </span>
            </div>
        </div>
    )
}

// ── Auto-refresh countdown ────────────────────────────────────────────────────
function RefreshCountdown({ seconds, onRefresh, refreshing }) {
    const pct = (seconds / 300) * 100

    return (
        <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-3 py-1.5
                       bg-[#1a1a2e] border border-[#2a2a3e]
                       rounded-lg text-xs text-gray-400
                       hover:text-white hover:border-blue-500/50
                       transition-all group"
            title={`Auto-refresh in ${seconds}s`}
        >
            <div className="relative w-4 h-4">
                <svg viewBox="0 0 16 16" className="w-4 h-4 -rotate-90">
                    <circle cx="8" cy="8" r="6"
                        fill="none" stroke="#2a2a3e" strokeWidth="2" />
                    <circle cx="8" cy="8" r="6"
                        fill="none"
                        stroke={refreshing ? '#3b82f6' : '#4b5563'}
                        strokeWidth="2"
                        strokeDasharray={`${2 * Math.PI * 6}`}
                        strokeDashoffset={`${2 * Math.PI * 6 * (1 - pct / 100)}`}
                        className="transition-all duration-1000"
                    />
                </svg>
                <RefreshCw
                    size={8}
                    className={`absolute inset-0 m-auto
                               ${refreshing
                                   ? 'animate-spin text-blue-400'
                                   : 'text-gray-500 group-hover:text-white'
                               }`}
                />
            </div>
            <span className="hidden sm:inline tabular-nums w-8 text-right">
                {refreshing ? '...' : `${seconds}s`}
            </span>
        </button>
    )
}

// ── Main Navbar ───────────────────────────────────────────────────────────────
export default function Navbar({ period, onPeriodChange, onRefresh, lastUpdated }) {
    const [refreshing,     setRefreshing]     = useState(false)
    const [marketData,     setMarketData]     = useState(null)
    const [vix,            setVix]            = useState(null)
    const [countdown,      setCountdown]      = useState(300) // 5 min
    const [pricesLoading,  setPricesLoading]  = useState(true)

    // ── Fetch market prices ───────────────────────────────────────────────────
    const loadPrices = useCallback(async () => {
        setPricesLoading(true)
        try {
            const [priceData, vixData] = await Promise.all([
                fetchMarketPrices(),
                fetchIndiaVix(),
            ])
            setMarketData(priceData)
            setVix(vixData?.current_vix ?? null)
        } catch (e) {
            console.error('Market fetch failed:', e)
        }
        setPricesLoading(false)
    }, [])
    // Initial load
    useEffect(() => {
        loadPrices()
    }, [loadPrices])

    // ── Countdown timer — refreshes prices every 5 minutes ───────────────────
    useEffect(() => {
        const tick = setInterval(() => {
            setCountdown(prev => {
                if (prev <= 1) {
                    loadPrices()   // auto-refresh prices
                    return 300     // reset to 5 min
                }
                return prev - 1
            })
        }, 1000)
        return () => clearInterval(tick)
    }, [loadPrices])

    // ── Manual refresh ────────────────────────────────────────────────────────
    async function handleRefresh() {
        setRefreshing(true)
        setCountdown(300)
        await Promise.all([loadPrices(), onRefresh()])
        setTimeout(() => setRefreshing(false), 1000)
    }

    const vixColor = !vix ? '#6b7280'
        : vix < 15  ? '#22c55e'
        : vix < 20  ? '#3b82f6'
        : vix < 25  ? '#f97316'
        : '#ef4444'

    const status = marketData?.market_status ?? 'Loading'
    const statusCfg = STATUS_CONFIG[status] ?? STATUS_CONFIG['Closed']
    const asOf = marketData?.as_of_ist ?? ''
    const prices = marketData?.prices ?? {}

    return (
        <nav className="sticky top-0 z-50 bg-[#0a0a0f]/98
                        backdrop-blur-md border-b border-[#1e1e2e]">
            <div className="max-w-screen-2xl mx-auto px-6
                            h-14 flex items-center justify-between gap-4">

                {/* ── Brand ────────────────────────────────────────────── */}
                <div className="flex items-center gap-3 shrink-0">
                    <div className="w-7 h-7 rounded-lg bg-blue-600
                                    flex items-center justify-center">
                        <TrendingUp size={14} className="text-white" />
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-white font-bold text-sm
                                         tracking-tight">
                            RiskLens
                        </span>
                        <span className="text-gray-600 text-xs">
                            Analytics
                        </span>
                    </div>

                    {/* Market status badge */}
                    <div className={`flex items-center gap-1.5 px-2 py-0.5
                                     ${statusCfg.bg} border ${statusCfg.border}
                                     rounded-full ml-1`}>
                        <div className={`w-1.5 h-1.5 rounded-full
                                         ${status === 'Open'
                                             ? 'animate-pulse'
                                             : ''}`}
                             style={{ backgroundColor: statusCfg.color }} />
                        <span className="text-xs font-medium"
                              style={{ color: statusCfg.color }}>
                            NSE {status}
                        </span>
                        {asOf && (
                            <span className="text-xs text-gray-700
                                             hidden xl:inline">
                                · {asOf}
                            </span>
                        )}
                    </div>
                </div>

                {/* ── Live price tickers ────────────────────────────── */}
                <div className="hidden lg:flex items-center flex-1
                                justify-center">
                    <div className="flex items-center bg-[#0f0f15]
                                    border border-[#1e1e2e] rounded-xl
                                    px-1 py-1.5">
                        <PriceTicker
                            label="Nifty 50"
                            data={prices.nifty50}
                            decimals={0}
                        />
                        <PriceTicker
                            label="Sensex"
                            data={prices.sensex}
                            decimals={0}
                        />
                        <PriceTicker
                            label="India VIX"
                            data={vix ? { price: vix, change_pct: 0 } : null}
                            decimals={2}
                        />
                        <PriceTicker
                            label="USD / INR"
                            data={prices.usdinr}
                            decimals={2}
                        />
                        <PriceTicker
                            label="Gold"
                            data={prices.gold}
                            prefix="$"
                            decimals={0}
                        />
                    </div>
                </div>

                {/* ── Controls ────────────────────────────────────── */}
                <div className="flex items-center gap-2 shrink-0">

                    {/* Last updated */}
                    {lastUpdated && (
                        <div className="hidden xl:flex items-center
                                        gap-1 text-xs text-gray-700">
                            <Clock size={10} />
                            <span>{lastUpdated}</span>
                        </div>
                    )}

                    {/* Period dropdown */}
                    <div className="relative">
                        <select
                            value={period}
                            onChange={e => onPeriodChange(Number(e.target.value))}
                            className="bg-[#1a1a2e] border border-[#2a2a3e]
                                       rounded-lg pl-3 pr-7 py-1.5 text-xs
                                       text-gray-300 font-medium
                                       focus:outline-none focus:border-blue-500/50
                                       cursor-pointer appearance-none"
                        >
                            <option value={1}>1 Year</option>
                            <option value={2}>2 Years</option>
                            <option value={3}>3 Years</option>
                        </select>
                        <div className="pointer-events-none absolute right-2
                                        top-1/2 -translate-y-1/2">
                            <svg width="10" height="10" viewBox="0 0 24 24"
                                 fill="none" stroke="#6b7280" strokeWidth="2">
                                <path d="M6 9l6 6 6-6"/>
                            </svg>
                        </div>
                    </div>

                    {/* Auto-refresh countdown button */}
                    <RefreshCountdown
                        seconds={countdown}
                        onRefresh={handleRefresh}
                        refreshing={refreshing}
                    />
                </div>
            </div>
        </nav>
    )
}