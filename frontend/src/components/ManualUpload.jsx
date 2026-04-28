import { useRef, useState } from 'react'
import { uploadManual } from '../api'

export default function ManualUpload({ onUploaded }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    try {
      const manual = await uploadManual(file)
      onUploaded(manual)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-full grid place-items-center p-6">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-sm border border-zinc-200 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-zinc-900">Bike Troubleshooting Bot</h1>
          <p className="mt-2 text-zinc-600 text-sm leading-relaxed">
            Upload your bike's Owner's Manual or Service Manual (PDF). The bot will only answer
            from what's actually in the document — no guesswork.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="w-full border-2 border-dashed border-zinc-300 rounded-xl py-10 text-center hover:border-zinc-400 hover:bg-zinc-50 transition"
          >
            <div className="text-zinc-700 font-medium">
              {file ? file.name : 'Click to choose a PDF'}
            </div>
            <div className="text-xs text-zinc-500 mt-1">
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
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}
          {/* Warnings from the server (sparse scan, large manual, etc.) are forwarded via onUploaded */}

          <button
            type="submit"
            disabled={!file || busy}
            className="w-full bg-zinc-900 text-white rounded-lg py-3 font-medium hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {busy ? 'Indexing manual…' : 'Upload and start chatting'}
          </button>
        </form>

        <p className="mt-6 text-xs text-zinc-500 leading-relaxed">
          Tip: scanned/image-only PDFs aren't supported in this demo. Use a text-based PDF.
        </p>
      </div>
    </div>
  )
}
