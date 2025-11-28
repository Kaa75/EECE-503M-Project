import React, { useState } from 'react'
import apiService from '../services/api'
import { Account } from '../types'

interface CreateAccountModalProps {
  onClose: () => void
  onCreated: (account: Account) => void
}

const CreateAccountModal: React.FC<CreateAccountModalProps> = ({ onClose, onCreated }) => {
  const [accountType, setAccountType] = useState<'checking' | 'savings' | ''>('')
  const [openingBalance, setOpeningBalance] = useState<string>('0')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')

    // Validation
    if (!accountType) {
      setError('Please select an account type')
      return
    }
    const amount = parseFloat(openingBalance)
    if (Number.isNaN(amount) || amount < 0) {
      setError('Opening balance must be a valid number >= 0')
      return
    }

    try {
      setLoading(true)
      const created = await apiService.createAccount({
        account_type: accountType,
        opening_balance: amount
      })
      onCreated(created)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create account'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
        <h2>Create New Account</h2>
        {error && <div className="alert alert-error mb-2">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Account Type</label>
            <select
              value={accountType}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                const val = e.target.value as 'checking' | 'savings' | ''
                setAccountType(val)
              }}
              required
            >
              <option value="">Select type</option>
              <option value="checking">Checking</option>
              <option value="savings">Savings</option>
            </select>
          </div>

          <div className="form-group">
            <label>Opening Balance</label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={openingBalance}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpeningBalance(e.target.value)}
              required
            />
          </div>

          <div className="flex gap-2 mt-2">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateAccountModal
