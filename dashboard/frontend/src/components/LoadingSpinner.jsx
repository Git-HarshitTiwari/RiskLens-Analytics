export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-48 gap-3">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
        <div className="absolute inset-1 rounded-full border-2 border-transparent border-t-indigo-400 animate-spin" 
             style={{ animationDirection: 'reverse', animationDuration: '0.6s' }} />
      </div>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  )
}

export function ErrorCard({ message }) {
  return (
    <div className="flex items-center gap-3 p-4 bg-red-950/30 border border-red-800/40 rounded-lg">
      <span className="text-red-400 text-lg">⚠</span>
      <p className="text-sm text-red-400">{message}</p>
    </div>
  )
}

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#16161e] border border-[#2a2a3e] rounded-xl p-4 ${className}`}>
      {children}
    </div>
  )
}

export function SectionTitle({ children }) {
  return (
    <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">
      {children}
    </h2>
  )
}