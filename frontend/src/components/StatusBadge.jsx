export default function StatusBadge({ online }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`w-2 h-2 rounded-full ${online ? 'bg-green-400' : 'bg-red-500'}`} />
      <span className="text-gray-400">{online ? 'Backend connected' : 'Backend offline'}</span>
    </div>
  )
}
