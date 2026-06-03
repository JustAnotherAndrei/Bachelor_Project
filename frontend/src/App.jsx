import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ChallengeProvider } from './contexts/ChallengeContext'
import Dashboard from './components/Dashboard'
import ChallengeMode from './components/challenge/ChallengeMode'

function App() {
  return (
    <AuthProvider>
      <ChallengeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/challenge" element={<ChallengeMode />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ChallengeProvider>
    </AuthProvider>
  )
}

export default App
