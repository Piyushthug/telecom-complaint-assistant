const STEP_LABELS = {
  analyze_sentiment: 'Analyzing Sentiment',
  categorization: 'Categorizing Complaint',
  summarize: 'Summarizing Issue',
  check_history: 'Checking History',
  rag_retrieve: 'Retrieving Policies',
  generate_response: 'Generating Response',
  validate: 'Validating Response',
}

const STEP_ORDER = [
  'analyze_sentiment',
  'categorization',
  'summarize',
  'check_history',
  'rag_retrieve',
  'generate_response',
  'validate',
]

export default function ProgressTracker({ steps }) {
  return (
    <div className="progress-section">
      <div className="progress-header">
        <div className="spinner"></div>
        <h2>Processing Complaint...</h2>
      </div>

      <div className="progress-steps">
        {STEP_ORDER.map((stepKey) => {
          const step = steps.find((s) => s.step === stepKey)
          const status = step?.status || 'pending'
          const message = step?.message || ''

          return (
            <div
              key={stepKey}
              className={`progress-step ${
                status === 'completed' ? 'completed' : status === 'started' ? 'active' : ''
              }`}
            >
              <div className="progress-step-icon">
                {status === 'completed' ? (
                  '✓'
                ) : status === 'started' ? (
                  <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                ) : (
                  '○'
                )}
              </div>
              <div className="progress-step-text">
                <div className="progress-step-label">{STEP_LABELS[stepKey]}</div>
                {message && <div className="progress-step-message">{message}</div>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
