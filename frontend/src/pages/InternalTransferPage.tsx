import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { Account } from '../types'

const InternalTransferPage: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [form, setForm] = useState({
    sender_account_id: '',
    receiver_account_id: '',
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
        // Ensure CSRF token present (safe to call; interceptor will attach for POST)
        await apiService.fetchCsrfToken()
      } catch {
        // Non-fatal; backend may not require for GET
      }
      try {
        if (user?.id) {
          const list = await apiService.getUserAccounts(user.id)
          setAccounts(list)
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load accounts'
        setError(message)
      }
    }
    init()
  }, [user])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (!form.sender_account_id || !form.receiver_account_id) {
      setError('Please select both accounts')
      return
    }
    if (form.sender_account_id === form.receiver_account_id) {
      setError('From and To accounts must be different')
      return
    }
    try {
      setLoading(true)
      await apiService.internalTransfer({
        sender_account_id: parseInt(form.sender_account_id),
        receiver_account_id: parseInt(form.receiver_account_id),
        amount: parseFloat(form.amount),
        description: form.description
      })
      setSuccess('Internal transfer completed successfully!')
      setForm({ sender_account_id: '', receiver_account_id: '', amount: '', description: '' })
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
      <h1>Internal Transfer</h1>

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
            <label>To Account (Your Account)</label>
            <select
              value={form.receiver_account_id}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setForm({ ...form, receiver_account_id: e.target.value })}
              required
            >
              <option value="">Select account</option>
              {accounts
                .filter(a => a.status === 'active' && a.id.toString() !== form.sender_account_id)
                .map(a => (
                  <option key={a.id} value={a.id.toString()}>
                    {a.account_number} - {a.account_type}
                  </option>
                ))}
            </select>
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

export default InternalTransferPage
