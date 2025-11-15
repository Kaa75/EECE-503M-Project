import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { Account, Transaction } from '../types'

const TransactionsPage: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showTransferForm, setShowTransferForm] = useState(false)
  const [transferType, setTransferType] = useState<'internal' | 'external'>('internal')
  
  const [transfer, setTransfer] = useState({
    from_account_id: '',
    to_account_id: '',
    to_account_number: '',
    amount: '',
    description: ''
  })

  const [filter, setFilter] = useState({
    account_id: '',
    start_date: '',
    end_date: '',
    transaction_type: '',
    min_amount: '',
    max_amount: ''
  })

  useEffect(() => {
    loadAccounts()
  }, [user])

  const loadAccounts = async () => {
    try {
      if (user?.id) {
        const accountList = await apiService.getUserAccounts(user.id)
        setAccounts(accountList)
        if (accountList.length > 0) {
          setFilter({ ...filter, account_id: accountList[0].id.toString() })
          loadTransactions(accountList[0].id)
        }
      }
    } catch (err) {
      setError('Failed to load accounts')
    }
  }

  const loadTransactions = async (accountId?: number) => {
    const id = accountId || parseInt(filter.account_id)
    if (!id) return

    try {
      setLoading(true)
      const result = await apiService.getAccountTransactions(id, 50, 0)
      setTransactions(result.transactions)
    } catch (err) {
      setError('Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterTransactions = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!filter.account_id) return

    try {
      setLoading(true)
      const filters: any = {}
      if (filter.start_date) filters.start_date = filter.start_date
      if (filter.end_date) filters.end_date = filter.end_date
      if (filter.transaction_type) filters.transaction_type = filter.transaction_type
      if (filter.min_amount) filters.min_amount = parseFloat(filter.min_amount)
      if (filter.max_amount) filters.max_amount = parseFloat(filter.max_amount)

      const result = await apiService.filterTransactions(parseInt(filter.account_id), filters)
      setTransactions(result.transactions)
    } catch (err) {
      setError('Failed to filter transactions')
    } finally {
      setLoading(false)
    }
  }

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      if (transferType === 'internal') {
        await apiService.internalTransfer({
          sender_account_id: parseInt(transfer.from_account_id),
          receiver_account_id: parseInt(transfer.to_account_id),
          amount: parseFloat(transfer.amount),
          description: transfer.description
        })
      } else {
        await apiService.externalTransfer({
          sender_account_id: parseInt(transfer.from_account_id),
          receiver_account_number: transfer.to_account_number,
          amount: parseFloat(transfer.amount),
          description: transfer.description
        })
      }
      
      setSuccess('Transfer completed successfully!')
      setShowTransferForm(false)
      setTransfer({ from_account_id: '', to_account_id: '', to_account_number: '', amount: '', description: '' })
      loadAccounts()
      loadTransactions()
    } catch (err: any) {
      setError(err.message || 'Transfer failed')
    }
  }

  return (
    <div className="transactions">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>Transactions</h1>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Transfer Button */}
        <div className="mb-3">
          <button 
            onClick={() => setShowTransferForm(!showTransferForm)}
            className="btn btn-primary"
          >
            {showTransferForm ? 'Cancel Transfer' : '💸 Make a Transfer'}
          </button>
        </div>

        {/* Transfer Form */}
        {showTransferForm && (
          <div className="card mb-3">
            <h2>New Transfer</h2>
            
            {/* Transfer Type Toggle */}
            <div className="transfer-type-toggle mb-2">
              <button
                className={`btn ${transferType === 'internal' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setTransferType('internal')}
              >
                Internal Transfer
              </button>
              <button
                className={`btn ${transferType === 'external' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setTransferType('external')}
              >
                External Transfer
              </button>
            </div>

            <form onSubmit={handleTransfer}>
              <div className="form-group">
                <label>From Account</label>
                <select
                  value={transfer.from_account_id}
                  onChange={(e) => setTransfer({ ...transfer, from_account_id: e.target.value })}
                  required
                >
                  <option value="">Select account</option>
                  {accounts.filter(a => a.status === 'active').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.account_number} - {account.account_type} (${account.balance.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              {transferType === 'internal' ? (
                <div className="form-group">
                  <label>To Account (Your Account)</label>
                  <select
                    value={transfer.to_account_id}
                    onChange={(e) => setTransfer({ ...transfer, to_account_id: e.target.value })}
                    required
                  >
                    <option value="">Select account</option>
                    {accounts.filter(a => a.status === 'active' && a.id.toString() !== transfer.from_account_id).map(account => (
                      <option key={account.id} value={account.id}>
                        {account.account_number} - {account.account_type}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="form-group">
                  <label>To Account Number</label>
                  <input
                    type="text"
                    value={transfer.to_account_number}
                    onChange={(e) => setTransfer({ ...transfer, to_account_number: e.target.value })}
                    placeholder="ACC-1234567890"
                    required
                  />
                </div>
              )}

              <div className="form-group">
                <label>Amount</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={transfer.amount}
                  onChange={(e) => setTransfer({ ...transfer, amount: e.target.value })}
                  placeholder="0.00"
                  required
                />
              </div>

              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  value={transfer.description}
                  onChange={(e) => setTransfer({ ...transfer, description: e.target.value })}
                  placeholder="Payment for..."
                />
              </div>

              <button type="submit" className="btn btn-primary">
                Complete Transfer
              </button>
            </form>
          </div>
        )}

        {/* Transaction Filter */}
        <div className="card mb-3">
          <h2>Filter Transactions</h2>
          <form onSubmit={handleFilterTransactions}>
            <div className="grid grid-2">
              <div className="form-group">
                <label>Account</label>
                <select
                  value={filter.account_id}
                  onChange={(e) => {
                    setFilter({ ...filter, account_id: e.target.value })
                    loadTransactions(parseInt(e.target.value))
                  }}
                >
                  {accounts.map(account => (
                    <option key={account.id} value={account.id}>
                      {account.account_number} - {account.account_type}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Transaction Type</label>
                <select
                  value={filter.transaction_type}
                  onChange={(e) => setFilter({ ...filter, transaction_type: e.target.value })}
                >
                  <option value="">All</option>
                  <option value="credit">Credit</option>
                  <option value="debit">Debit</option>
                </select>
              </div>

              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={filter.start_date}
                  onChange={(e) => setFilter({ ...filter, start_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={filter.end_date}
                  onChange={(e) => setFilter({ ...filter, end_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Min Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={filter.min_amount}
                  onChange={(e) => setFilter({ ...filter, min_amount: e.target.value })}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>Max Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={filter.max_amount}
                  onChange={(e) => setFilter({ ...filter, max_amount: e.target.value })}
                  placeholder="0.00"
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary">
              Apply Filters
            </button>
          </form>
        </div>

        {/* Transaction History */}
        <div className="card">
          <h2>Transaction History</h2>
          
          {loading ? (
            <p>Loading transactions...</p>
          ) : transactions.length === 0 ? (
            <p className="text-muted">No transactions found</p>
          ) : (
            <div className="transaction-table">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Transaction ID</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((txn) => (
                    <tr key={txn.transaction_id}>
                      <td>{new Date(txn.created_at).toLocaleString()}</td>
                      <td><small>{txn.transaction_id}</small></td>
                      <td>
                        <span className={`badge badge-${txn.transaction_type}`}>
                          {txn.transaction_type}
                        </span>
                      </td>
                      <td>{txn.description || 'N/A'}</td>
                      <td className={`transaction-amount ${txn.transaction_type}`}>
                        {txn.transaction_type === 'credit' ? '+' : '-'}
                        ${Math.abs(txn.amount).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TransactionsPage
