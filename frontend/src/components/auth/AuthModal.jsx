import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import ForgotPasswordForm from './ForgotPasswordForm'
import ResetPasswordForm from './ResetPasswordForm'

export default function AuthModal({ open, onClose, initialView = 'login', initialToken = '' }) {
  const [view, setView] = useState(initialView)
  const [resetToken, setResetToken] = useState(initialToken)

  useEffect(() => {
    if (open) {
      setView(initialView)
      setResetToken(initialToken)
    }
  }, [open, initialView, initialToken])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md mx-4 bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-200 p-1 rounded-md"
          aria-label="Close"
        >
          <X size={18} />
        </button>

        {view === 'login' && (
          <LoginForm
            onSuccess={onClose}
            onSwitchToRegister={() => setView('register')}
            onSwitchToForgot={() => setView('forgot')}
          />
        )}
        {view === 'register' && (
          <RegisterForm
            onSuccess={onClose}
            onSwitchToLogin={() => setView('login')}
          />
        )}
        {view === 'forgot' && (
          <ForgotPasswordForm
            onUseToken={(t) => { setResetToken(t); setView('reset') }}
            onSwitchToLogin={() => setView('login')}
          />
        )}
        {view === 'reset' && (
          <ResetPasswordForm
            initialToken={resetToken}
            onSuccess={onClose}
            onSwitchToLogin={() => setView('login')}
          />
        )}
      </div>
    </div>
  )
}
