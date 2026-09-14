import { useState } from 'react'
import ComplaintForm from './components/ComplaintForm'
import ProgressTracker from './components/ProgressTracker'
import ResultsDisplay from './components/ResultsDisplay'

export default function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState([])
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (formData) => {
    setIsLoading(true)
    setProgress([])
    setResult(null)
    setError(null)

    try {
      const response = await fetch('/api/complaint-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines[lines.length - 1]

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i]
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'progress') {
                setProgress((prev) => {
                  const updated = [...prev]
                  const existing = updated.findIndex((p) => p.step === data.step)
                  if (existing >= 0) {
                    updated[existing] = { ...data }
                  } else {
                    updated.push(data)
                  }
                  return updated
                })
              } else if (data.type === 'result') {
                setResult(data.data)
                setIsLoading(false)
              } else if (data.type === 'error') {
                setError(data.message)
                setIsLoading(false)
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred while processing your complaint')
      setIsLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>📞 Telecom Complaint Assistant</h1>
        <p>Instant AI-powered resolution for customer support</p>
      </div>

      <div className="main-content">
        <div className="card">
          <ComplaintForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {isLoading && (
          <div className="card">
            <ProgressTracker steps={progress} />
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
      {result && <ResultsDisplay result={result} />}
    </div>
  )
}
