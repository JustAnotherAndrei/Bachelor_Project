import { useState } from 'react'
import { Lock, KeyRound, Check } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function ResetPasswordForm({ initialToken = '', onSuccess, onSwitchToLogin }) {
  const { resetPassword } = useAuth()
  const [token, setToken] = useState(initialToken)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setSubmitting(true)
    try {
      await resetPassword(token, password)
      onSuccess?.()
    } catch (err) {
      setError(err.detail || 'Reset failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-100">Set new password</h2>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">Reset token</span>
        <div className="relative">
          <KeyRound size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            required
            value={token}
            onChange={e => setToken(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 font-mono focus:border-violet-500 focus:outline-none"
          />
        </div>
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">New password</span>
        <div className="relative">
          <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 focus:border-violet-500 focus:outline-none"
          />
        </div>
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">Confirm new password</span>
        <div className="relative">
          <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="password"
            required
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 focus:border-violet-500 focus:outline-none"
          />
        </div>
      </label>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm rounded-lg px-4 py-2.5 transition-colors"
      >
        <Check size={14} />
        {submitting ? 'Updating…' : 'Set new password'}
      </button>

      <button type="button" onClick={onSwitchToLogin} className="text-xs text-gray-500 hover:text-violet-300">
        Back to sign in
      </button>
    </form>
  )
}
