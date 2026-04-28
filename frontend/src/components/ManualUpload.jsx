import { useRef, useState } from 'react'
import { uploadManual } from '../api'

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
    </svg>
  )
}

const STEPS = ['Reading pages…', 'Extracting text…', 'Almost ready…']

export default function ManualUpload({ onUploaded, dark, onToggleDark }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    setStep(0)
    const ticker = setInterval(() => setStep(s => Math.min(s + 1, STEPS.length - 1)), 1200)
    try {
      const manual = await uploadManual(file)
      onUploaded(manual)
    } catch (err) {
      setError(err.message)
    } finally {
      clearInterval(ticker)
      setBusy(false)
    }
  }

  return (
    <div className="min-h-full grid place-items-center p-6 bg-white dark:bg-zinc-950 transition-colors">
      <div className="w-full max-w-xl">
        <div className="flex justify-end mb-4">
          <button
            onClick={onToggleDark}
            className="p-2 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
        </div>

        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Bike Troubleshooting Bot</h1>
            <p className="mt-2 text-zinc-500 dark:text-zinc-400 text-sm leading-relaxed">
              Upload your bike's Owner's Manual or Service Manual (PDF). The bot will only answer
              from what's actually in the document — no guesswork.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="w-full border-2 border-dashed border-zinc-300 dark:border-zinc-700 rounded-xl py-10 text-center hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition"
            >
              <div className="text-zinc-700 dark:text-zinc-300 font-medium">
                {file ? file.name : 'Click to choose a PDF'}
              </div>
              <div className="text-xs text-zinc-500 dark:text-zinc-500 mt-1">
                {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : 'Royal Enfield, TVS, Honda, Yamaha…'}
              </div>
            </button>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />

            {error && (
              <div className="text-sm text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!file || busy}
              className="w-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-lg py-3 font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
            >
              {busy ? (
                <>
                  <Spinner />
                  <span>{STEPS[step]}</span>
                </>
              ) : (
                'Upload and start chatting'
              )}
            </button>
          </form>

          <p className="mt-6 text-xs text-zinc-400 dark:text-zinc-600 leading-relaxed">
            Tip: scanned/image-only PDFs aren't supported in this demo. Use a text-based PDF.
          </p>
        </div>
      </div>
    </div>
  )
}
