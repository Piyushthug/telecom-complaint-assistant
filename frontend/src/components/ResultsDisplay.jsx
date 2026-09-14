export default function ResultsDisplay({ result }) {
  const getSentimentBadgeClass = (sentiment) => {
    switch (sentiment?.toUpperCase()) {
      case 'POSITIVE':
        return 'positive'
      case 'NEUTRAL':
        return 'neutral'
      case 'NEGATIVE':
        return 'negative'
      case 'VERY_NEGATIVE':
        return 'very-negative'
      default:
        return 'neutral'
    }
  }

  const getValidationBadgeClass = (status) => {
    switch (status?.toUpperCase()) {
      case 'PASS':
        return 'pass'
      case 'FAIL':
        return 'fail'
      case 'ESCALATED':
        return 'escalated'
      default:
        return 'fail'
    }
  }

  return (
    <>
      <div className="success-message">✓ Complaint analyzed successfully</div>

      <div className="card">
        <h2 style={{ marginBottom: '20px', color: '#333' }}>Analysis Results</h2>

        <div className="results">
          <div className="result-card">
            <h3>Category</h3>
            <p>{result.category || 'N/A'}</p>
          </div>

          <div className="result-card">
            <h3>Sentiment</h3>
            <p>
              {result.sentiment || 'N/A'}
              <span className={`sentiment-badge ${getSentimentBadgeClass(result.sentiment)}`}>
                {result.sentiment}
              </span>
            </p>
          </div>

          <div className="result-card">
            <h3>Repeated Contact</h3>
            <p>{result.repeated_contact ? '⚠️ Yes' : '✓ No'}</p>
          </div>

          <div className="result-card">
            <h3>Validation Status</h3>
            <p>
              {result.validation_status || 'N/A'}
              <span className={`status-badge ${getValidationBadgeClass(result.validation_status)}`}>
                {result.validation_status}
              </span>
            </p>
          </div>

          <div className="result-card full-width">
            <h3>Summary</h3>
            <p>{result.summary || 'No summary available'}</p>
          </div>

          <div className="result-card full-width">
            <h3>Suggested Response</h3>
            <p
              style={{
                whiteSpace: 'pre-wrap',
                backgroundColor: '#f9f9f9',
                padding: '12px',
                borderRadius: '6px',
                marginTop: '8px',
              }}
            >
              {result.response || 'No response generated'}
            </p>
          </div>

          {result.validation_reason && (
            <div className="result-card full-width">
              <h3>Validation Details</h3>
              <p>{result.validation_reason}</p>
            </div>
          )}
        </div>

        {result.policy_sources && result.policy_sources.length > 0 && (
          <div className="policy-sources">
            <h3>📚 Policy Sources</h3>
            {result.policy_sources.map((source, idx) => (
              <div key={idx} className="source-item">
                <div className="source-item-title">
                  {source.document}
                  <span className="source-item-score">
                    Relevance: {(source.similarity_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="source-item-text">"{source.chunk_text.substring(0, 300)}..."</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
