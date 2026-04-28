import { useEffect, useState } from 'react'
import ManualUpload from './components/ManualUpload'
import ChatScreen from './components/ChatScreen'
import { checkHealth } from './api'

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

export default function App() {
  const [manual, setManual] = useState(null)
  const [healthWarning, setHealthWarning] = useState('')
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

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
    <div className="h-full flex flex-col bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 transition-colors">
      {healthWarning && (
        <div className="bg-amber-50 dark:bg-amber-950 text-amber-900 dark:text-amber-200 text-xs text-center px-4 py-1.5 border-b border-amber-200 dark:border-amber-800">
          {healthWarning}
        </div>
      )}
      <div className="flex-1 min-h-0 relative">
        {manual ? (
          <ChatScreen manual={manual} onChangeManual={() => setManual(null)} dark={dark} onToggleDark={() => setDark(d => !d)} />
        ) : (
          <ManualUpload onUploaded={setManual} dark={dark} onToggleDark={() => setDark(d => !d)} />
        )}
      </div>
    </div>
  )
}
