import { useState } from 'react'
import { Search, X } from 'lucide-react'

const SECTORS = {
  'Banking':  ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
  'IT':       ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM'],
  'Energy':   ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'BHARTIARTL'],
  'Consumer': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'ASIANPAINT', 'TITAN'],
  'Auto':     ['MARUTI', 'TATAMOTORS', 'BAJFINANCE', 'BAJAJFINSV', 'ADANIENT'],
  'Metals':   ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'ULTRACEMCO', 'LT'],
  'Pharma':   ['SUNPHARMA'],
}

export default function StockSelector({ selected, onChange }) {
  const [search, setSearch] = useState('')
  const [open, setOpen]     = useState(false)

  const allStocks = Object.values(SECTORS).flat()

  const filtered = search
    ? allStocks.filter(s => s.toLowerCase().includes(search.toLowerCase()))
    : allStocks

  function toggleStock(stock) {
    if (selected.includes(stock)) {
      onChange(selected.filter(s => s !== stock))
    } else if (selected.length < 10) {
      onChange([...selected, stock])
    }
  }

  function selectSector(sector) {
    const sectorStocks = SECTORS[sector]
    const allSelected  = sectorStocks.every(s => selected.includes(s))
    if (allSelected) {
      onChange(selected.filter(s => !sectorStocks.includes(s)))
    } else {
      const merged = [...new Set([...selected, ...sectorStocks])].slice(0, 10)
      onChange(merged)
    }
  }

  return (
    <div className="bg-[#16161e] border border-[#2a2a3e] rounded-xl p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Stock Filter
          <span className="ml-2 text-blue-500 normal-case font-normal">
            ({selected.length}/10 selected)
          </span>
        </h2>
        <button
          onClick={() => setOpen(!open)}
          className="text-xs text-gray-500 hover:text-white transition-colors"
        >
          {open ? 'Collapse ↑' : 'Expand ↓'}
        </button>
      </div>

      {/* Selected chips */}
      <div className="flex flex-wrap gap-2 mb-3">
        {selected.map(stock => (
          <div key={stock}
               className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-950/50 
                          border border-blue-700/40 rounded-full">
            <span className="text-xs text-blue-300 font-mono font-semibold">
              {stock}
            </span>
            <button onClick={() => toggleStock(stock)}
                    className="text-blue-500 hover:text-red-400 transition-colors">
              <X size={10} />
            </button>
          </div>
        ))}
        {selected.length === 0 && (
          <span className="text-xs text-gray-600">
            No filter — showing all 30 stocks
          </span>
        )}
      </div>

      {open && (
        <>
          {/* Search */}
          <div className="relative mb-3">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search stock..."
              className="w-full bg-[#0f0f13] border border-[#2a2a3e] rounded-lg 
                         pl-8 pr-3 py-2 text-xs text-gray-300 
                         placeholder-gray-600 focus:outline-none 
                         focus:border-blue-600/50"
            />
          </div>

          {/* Sector quick-select */}
          {!search && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {Object.keys(SECTORS).map(sector => (
                <button
                  key={sector}
                  onClick={() => selectSector(sector)}
                  className="px-2.5 py-1 bg-[#0f0f13] border border-[#2a2a3e] 
                             rounded-lg text-xs text-gray-400 
                             hover:border-blue-600/50 hover:text-blue-400 
                             transition-all"
                >
                  {sector}
                </button>
              ))}
            </div>
          )}

          {/* Stock grid */}
          <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-1.5">
            {filtered.map(stock => {
              const isSelected = selected.includes(stock)
              return (
                <button
                  key={stock}
                  onClick={() => toggleStock(stock)}
                  className={`px-2 py-1.5 rounded-lg text-xs font-mono font-semibold 
                              transition-all border
                              ${isSelected
                                ? 'bg-blue-600 border-blue-500 text-white'
                                : 'bg-[#0f0f13] border-[#2a2a3e] text-gray-500 hover:text-white hover:border-[#3a3a5e]'
                              }`}
                >
                  {stock}
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}