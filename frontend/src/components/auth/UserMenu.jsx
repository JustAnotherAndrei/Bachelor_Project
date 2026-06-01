import { useState, useRef, useEffect } from 'react'
import { LogOut, User, ChevronDown, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  if (!user) return null

  const initials = (user.full_name || user.email)
    .split(/\s+|@/)
    .filter(Boolean)
    .slice(0, 2)
    .map(s => s[0].toUpperCase())
    .join('')

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
      >
        {user.avatar_url ? (
          <img src={user.avatar_url} alt="" className="w-7 h-7 rounded-full" />
        ) : (
          <div className="w-7 h-7 rounded-full bg-violet-600 text-white text-xs font-semibold flex items-center justify-center">
            {initials}
          </div>
        )}
        <div className="text-left hidden sm:block">
          <p className="text-xs text-gray-100 font-medium leading-tight">
            {user.full_name || user.email.split('@')[0]}
          </p>
          <p className="text-[10px] text-gray-500 leading-tight">{user.email}</p>
        </div>
        <ChevronDown size={14} className="text-gray-500" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-gray-900 border border-gray-800 rounded-xl shadow-xl py-2 z-50">
          <div className="px-4 py-2 border-b border-gray-800">
            <p className="text-sm text-gray-100 font-medium">{user.full_name || 'No name set'}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {user.has_password && (
                <span className="text-[10px] text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">password</span>
              )}
              {user.has_google && (
                <span className="text-[10px] text-blue-300 bg-blue-950 px-1.5 py-0.5 rounded">Google</span>
              )}
              {user.is_email_verified && (
                <span className="text-[10px] text-emerald-300 bg-emerald-950 px-1.5 py-0.5 rounded flex items-center gap-1">
                  <ShieldCheck size={9} /> verified
                </span>
              )}
            </div>
          </div>

          <button
            disabled
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-500 cursor-not-allowed"
          >
            <User size={14} /> Profile <span className="ml-auto text-[10px]">soon</span>
          </button>

          <button
            onClick={() => { setOpen(false); logout() }}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-300 hover:bg-red-950 transition-colors"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      )}
    </div>
  )
}
