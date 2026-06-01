import { useState } from 'react'
import { Mail, Send, KeyRound, Copy, ExternalLink, AlertTriangle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function ForgotPasswordForm({ onUseToken, onSwitchToLogin }) {
  const { forgotPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const data = await forgotPassword(email)
      setResult(data)
    } catch (err) {
      setError(err.detail || 'Request failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (result) {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold text-gray-100">Reset link issued</h2>

        <div className="flex items-start gap-3 bg-yellow-950 border border-yellow-800 rounded-lg px-4 py-3">
          <AlertTriangle className="text-yellow-400 shrink-0 mt-0.5" size={16} />
          <p className="text-xs text-yellow-300">
            <strong>Dev mode:</strong> the reset link is shown below. In a real deployment it
            would be delivered by email. Single-use, expires in 15 minutes.
          </p>
        </div>

        {result.dev_reset_token && (
          <div className="flex flex-col gap-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5">
            <span className="text-xs text-gray-500">Reset token</span>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs text-emerald-300 font-mono break-all">
                {result.dev_reset_token}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(result.dev_reset_token)}
                className="text-gray-400 hover:text-emerald-300"
                title="Copy token"
              >
                <Copy size={14} />
              </button>
            </div>
          </div>
        )}

        <button
          onClick={() => onUseToken?.(result.dev_reset_token)}
          className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm rounded-lg px-4 py-2.5 transition-colors"
        >
          <KeyRound size={14} />
          Use this token to set a new password
        </button>

        {result.dev_reset_url && (
          <a
            href={result.dev_reset_url}
            className="flex items-center justify-center gap-2 text-xs text-violet-300 hover:text-violet-200"
          >
            <ExternalLink size={12} /> {result.dev_reset_url}
          </a>
        )}

        <button onClick={onSwitchToLogin} className="text-xs text-gray-500 hover:text-violet-300">
          Back to sign in
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-gray-100">Forgot password</h2>
      <p className="text-xs text-gray-500">
        Enter your email and we'll issue a single-use reset token (valid 15 minutes).
      </p>

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

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm rounded-lg px-4 py-2.5 transition-colors"
      >
        <Send size={14} />
        {submitting ? 'Sending…' : 'Send reset link'}
      </button>

      <button type="button" onClick={onSwitchToLogin} className="text-xs text-gray-500 hover:text-violet-300">
        Back to sign in
      </button>
    </form>
  )
}
