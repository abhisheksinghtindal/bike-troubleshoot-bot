import { useEffect, useState } from 'react'
import ManualUpload from './components/ManualUpload'
import ChatScreen from './components/ChatScreen'
import { checkHealth } from './api'

export default function App() {
  const [manual, setManual] = useState(null)
  const [healthWarning, setHealthWarning] = useState('')

  useEffect(() => {
    checkHealth()
      .then((h) => {
        if (!h.anthropic_key_configured) {
          setHealthWarning('Backend is missing ANTHROPIC_API_KEY — set it in the backend .env before chatting.')
        }
      })
      .catch(() => setHealthWarning('Cannot reach backend. Check VITE_API_URL.'))
  }, [])

  return (
    <div className="h-full flex flex-col">
      {healthWarning && (
        <div className="bg-amber-50 text-amber-900 text-xs text-center px-4 py-1.5 border-b border-amber-200">
          {healthWarning}
        </div>
      )}
      <div className="flex-1 min-h-0">
        {manual ? (
          <ChatScreen manual={manual} onChangeManual={() => setManual(null)} />
        ) : (
          <ManualUpload onUploaded={setManual} />
        )}
      </div>
    </div>
  )
}
