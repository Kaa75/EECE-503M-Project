import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import { Account } from '../types'

const ExternalTransferPage: React.FC = () => {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    sender_account_id: '',
    receiver_account_number: '',
    amount: '',
    description: ''
  })
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const init = async (): Promise<void> => {
      try {
        await apiService.fetchCsrfToken()
      } catch {}
      try {
        // Load user's accounts for dropdown
        const list = await apiService.getDashboard()
        const acctList = (list.accounts || []) as Account[]
        setAccounts(acctList as unknown as Account[])
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load accounts'
        // Show inline error later on submit to avoid blocking
        console.warn(message)
      }
    }
    init()
  }, [])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (!form.sender_account_id) {
      setError('Please select a sender account')
      return
    }
    if (!form.receiver_account_number) {
      setError('Please enter a valid receiver account number')
      return
    }
    try {
      setLoading(true)
      await apiService.externalTransfer({
        sender_account_id: parseInt(form.sender_account_id),
        receiver_account_number: form.receiver_account_number,
        amount: parseFloat(form.amount),
        description: form.description
      })
      setSuccess('External transfer completed successfully!')
      setForm({ sender_account_id: '', receiver_account_number: '', amount: '', description: '' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Transfer failed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <button className="btn btn-secondary mb-2" onClick={() => navigate('/dashboard')}>← Back</button>
      <h1>External Transfer</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>From Account</label>
            <select
              value={form.sender_account_id}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setForm({ ...form, sender_account_id: e.target.value })}
              required
            >
              <option value="">Select account</option>
              {accounts.filter(a => a.status === 'active').map(a => (
                <option key={a.id} value={a.id.toString()}>
                  {a.account_number} - {a.account_type} (${a.balance.toFixed(2)})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>To Account Number</label>
            <input
              type="text"
              value={form.receiver_account_number}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, receiver_account_number: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Amount</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={form.amount}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, amount: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Description (optional)</label>
            <input
              type="text"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Processing...' : 'Submit Transfer'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ExternalTransferPage
