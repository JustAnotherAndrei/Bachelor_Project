import { useState } from 'react'
import { Mail, Lock, User, UserPlus } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import GoogleSignInButton from './GoogleSignInButton'

export default function RegisterForm({ onSuccess, onSwitchToLogin }) {
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setSubmitting(true)
    try {
      await register(email, password, fullName || null)
      onSuccess?.()
    } catch (err) {
      setError(err.detail || 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-100">Create your account</h2>

      <GoogleSignInButton label="Sign up with Google" />

      <div className="flex items-center gap-2 text-xs text-gray-600">
        <div className="flex-1 h-px bg-gray-800" />
        <span>or</span>
        <div className="flex-1 h-px bg-gray-800" />
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="text-xs text-gray-400">Full name <span className="text-gray-600">(optional)</span></span>
        <div className="relative">
          <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={fullName}
            onChange={e => setFullName(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 focus:border-violet-500 focus:outline-none"
            placeholder="Alice Quantum"
          />
        </div>
      </label>

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
        <span className="text-xs text-gray-400">Password <span className="text-gray-600">(min 8 chars)</span></span>
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
        <span className="text-xs text-gray-400">Confirm password</span>
        <div className="relative">
          <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="password"
            required
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
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
        <UserPlus size={14} />
        {submitting ? 'Creating account…' : 'Create account'}
      </button>

      <div className="text-xs text-gray-500 text-center">
        Already have an account?{' '}
        <button type="button" onClick={onSwitchToLogin} className="text-violet-300 hover:text-violet-200">
          Sign in
        </button>
      </div>
    </form>
  )
}
