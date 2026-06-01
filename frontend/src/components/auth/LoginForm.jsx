import { useState } from 'react'
import { Mail, Lock, LogIn } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import GoogleSignInButton from './GoogleSignInButton'

export default function LoginForm({ onSuccess, onSwitchToRegister, onSwitchToForgot }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      onSuccess?.()
    } catch (err) {
      setError(err.detail || 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-100">Sign in to Sequre</h2>

      <GoogleSignInButton />

      <div className="flex items-center gap-2 text-xs text-gray-600">
        <div className="flex-1 h-px bg-gray-800" />
        <span>or</span>
        <div className="flex-1 h-px bg-gray-800" />
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">Email</span>
        <div className="relative">
          <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 focus:border-violet-500 focus:outline-none"
            placeholder="you@example.com"
          />
        </div>
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">Password</span>
        <div className="relative">
          <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 focus:border-violet-500 focus:outline-none"
            placeholder="••••••••"
          />
        </div>
      </label>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm rounded-lg px-4 py-2.5 transition-colors"
      >
        <LogIn size={14} />
        {submitting ? 'Signing in…' : 'Sign in'}
      </button>

      <div className="flex justify-between text-xs text-gray-500">
        <button type="button" onClick={onSwitchToForgot} className="hover:text-violet-300">
          Forgot password?
        </button>
        <button type="button" onClick={onSwitchToRegister} className="hover:text-violet-300">
          Create account
        </button>
      </div>
    </form>
  )
}
