import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { askQuestion } from '../api'

function PageBadges({ text }) {
  const re = /\((?:pp?\.\s*)(\d+(?:\s*[\u2013-]\s*\d+)?)\)/g
  const matches = [...text.matchAll(re)]
  const seen = new Set()
  const pages = []
  for (const m of matches) {
    if (!seen.has(m[1])) { seen.add(m[1]); pages.push(m[1]) }
  }
  if (pages.length === 0) return null
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {pages.map((p) => (
        <span key={p} className="text-[11px] bg-zinc-100 text-zinc-700 rounded px-1.5 py-0.5 border border-zinc-200">
          p. {p}
        </span>
      ))}
    </div>
  )
}

export default function ChatScreen({ manual, onChangeManual }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (image) {
      const url = URL.createObjectURL(image)
      setImagePreview(url)
      return () => URL.revokeObjectURL(url)
    }
    setImagePreview(null)
  }, [image])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  function handleReset() {
    setMessages([])
    setInput('')
    setImage(null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const q = input.trim()
    if (!q || busy) return

    const userMsg = { role: 'user', text: q, imagePreview }
    setMessages((m) => [...m, userMsg])
    setInput('')
    const sentImage = image
    setImage(null)
    setBusy(true)

    try {
      const history = messages.map((m) => ({ role: m.role, text: m.text }))
      const result = await askQuestion({ manualId: manual.id, question: q, image: sentImage, history })
      setMessages((m) => [...m, {
        role: 'assistant',
        text: result.answer,
        warning: result.warning || null,
        usage: result.usage,
      }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', text: `Error: ${err.message}`, error: true }])
    } finally {
      setBusy(false)
    }
  }

  function handlePickImage(e) {
    const f = e.target.files?.[0]
    if (f) setImage(f)
  }

  return (
    <div className="min-h-full flex flex-col">
      {/* Top bar */}
      <header className="bg-white border-b border-zinc-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-8 w-8 rounded-lg bg-zinc-900 text-white grid place-items-center text-sm font-semibold">B</div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-zinc-900 truncate">{manual.filename}</div>
            <div className="text-xs text-zinc-500">{manual.page_count} pages · ~{manual.approx_tokens.toLocaleString()} tokens</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={handleReset}
              className="text-sm text-zinc-500 hover:text-zinc-900 px-3 py-1.5 rounded-md hover:bg-zinc-100"
              title="Clear conversation"
            >
              New chat
            </button>
          )}
          <button
            onClick={onChangeManual}
            className="text-sm text-zinc-600 hover:text-zinc-900 px-3 py-1.5 rounded-md hover:bg-zinc-100"
          >
            Change manual
          </button>
        </div>
      </header>

      {/* Manual warnings from upload */}
      {manual.warnings?.map((w, i) => (
        <div key={i} className="bg-amber-50 text-amber-900 text-xs text-center px-4 py-1.5 border-b border-amber-200">
          {w}
        </div>
      ))}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto thin-scroll">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-zinc-500 text-sm mt-12">
              <p className="mb-2">Ask about a problem with your bike.</p>
              <p className="text-xs">e.g. "Why is white smoke coming from the exhaust?" — or attach a photo.</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={
                  m.role === 'user'
                    ? 'max-w-[85%] bg-zinc-900 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm whitespace-pre-wrap'
                    : `max-w-[85%] bg-white border ${m.error ? 'border-red-200 text-red-700' : 'border-zinc-200 text-zinc-900'} rounded-2xl rounded-bl-sm px-4 py-3 text-sm`
                }
              >
                {m.imagePreview && (
                  <img src={m.imagePreview} alt="" className="rounded-lg mb-2 max-h-48 object-cover" />
                )}
                {m.role === 'assistant' && !m.error ? (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                      ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                      li: ({ children }) => <li>{children}</li>,
                      code: ({ children }) => <code className="bg-zinc-100 rounded px-1 text-xs">{children}</code>,
                    }}
                  >
                    {m.text}
                  </ReactMarkdown>
                ) : (
                  m.text
                )}
                {m.role === 'assistant' && !m.error && <PageBadges text={m.text} />}
                {m.warning && (
                  <div className="mt-2 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                    ⚠ {m.warning}
                  </div>
                )}
              </div>
            </div>
          ))}

          {busy && (
            <div className="flex justify-start">
              <div className="bg-white border border-zinc-200 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-zinc-500">
                Reading the manual<span className="inline-block animate-pulse">…</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Composer */}
      <div className="border-t border-zinc-200 bg-white">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4 py-3">
          {imagePreview && (
            <div className="mb-2 inline-flex items-center gap-2 bg-zinc-100 rounded-lg p-2">
              <img src={imagePreview} alt="preview" className="h-12 w-12 rounded object-cover" />
              <button
                type="button"
                onClick={() => setImage(null)}
                className="text-xs text-zinc-600 hover:text-zinc-900 px-2 py-1 rounded hover:bg-zinc-200"
              >
                Remove
              </button>
            </div>
          )}
          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="shrink-0 h-10 w-10 grid place-items-center rounded-lg border border-zinc-300 hover:bg-zinc-50"
              title="Attach an image"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
            </button>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/gif,image/webp" className="hidden" onChange={handlePickImage} />
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) } }}
              rows={1}
              placeholder="Ask about your bike…"
              className="flex-1 resize-none border border-zinc-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent max-h-40"
            />
            <button
              type="submit"
              disabled={!input.trim() || busy}
              className="shrink-0 h-10 px-4 bg-zinc-900 text-white text-sm rounded-lg hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
          <p className="mt-2 text-[11px] text-zinc-400 text-center">
            Answers come strictly from the uploaded manual. The bot will say so when something isn't covered.
          </p>
        </form>
      </div>
    </div>
  )
}
