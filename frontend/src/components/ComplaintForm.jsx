import { useState } from 'react'

export default function ComplaintForm({ onSubmit, isLoading }) {
  const [customerId, setCustomerId] = useState('')
  const [complaint, setComplaint] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (customerId.trim() && complaint.trim()) {
      onSubmit({
        customer_id: customerId,
        complaint: complaint,
      })
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2 style={{ marginBottom: '20px', color: '#333' }}>Submit a Complaint</h2>

      <div className="form-group">
        <label htmlFor="customer_id">Customer ID</label>
        <input
          id="customer_id"
          type="text"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="e.g., CUST0025"
          disabled={isLoading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="complaint">Complaint Details</label>
        <textarea
          id="complaint"
          value={complaint}
          onChange={(e) => setComplaint(e.target.value)}
          placeholder="Describe the issue you're experiencing..."
          disabled={isLoading}
          required
        />
      </div>

      <button type="submit" className="btn" disabled={isLoading}>
        {isLoading ? 'Processing...' : 'Analyze Complaint'}
      </button>
    </form>
  )
}
