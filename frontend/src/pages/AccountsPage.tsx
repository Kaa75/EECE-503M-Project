import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { Account, Transaction } from '../types'

const AccountsPage: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [recentTransactions, setRecentTransactions] = useState<{ [key: number]: Transaction[] }>({})
  
  const [newAccount, setNewAccount] = useState<{
    account_type: 'checking' | 'savings'
    opening_balance: string
  }>({
    account_type: 'checking',
    opening_balance: ''
  })

  useEffect(() => {
    loadAccounts()
  }, [user])

  const loadAccounts = async (): Promise<void> => {
    try {
      setLoading(true)
      setError('')
      if (user?.id) {
        console.log('Loading accounts for user:', user.id)
        const accountList = await apiService.getUserAccounts(user.id)
        console.log('Received accounts:', accountList)
        setAccounts(accountList)
        
        // Load recent transactions for each account
        for (const account of accountList) {
          loadRecentTransactions(account.id)
        }
      }
    } catch (err: unknown) {
      console.error('Error loading accounts:', err)
      const message = err instanceof Error ? err.message : 'Failed to load accounts'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const loadRecentTransactions = async (accountId: number): Promise<void> => {
    try {
      const result = await apiService.getAccountTransactions(accountId, 5, 0)
      setRecentTransactions(prev => ({
        ...prev,
        [accountId]: result.transactions
      }))
    } catch (err: unknown) {
      console.error('Failed to load transactions for account:', accountId)
    }
  }

  const handleCreateAccount = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault()
    try {
      setError('')
      console.log('Creating account:', newAccount)
      const result = await apiService.createAccount({
        account_type: newAccount.account_type,
        opening_balance: parseFloat(newAccount.opening_balance)
      })
      console.log('Account created:', result)
      setShowCreateForm(false)
      setNewAccount({ account_type: 'checking', opening_balance: '' })
      loadAccounts()
    } catch (err: unknown) {
      console.error('Error creating account:', err)
      const message = err instanceof Error ? err.message : 'Failed to create account'
      setError(message)
    }
  }

  if (loading) {
    return (
      <div className="accounts">
        <div className="container">
          <h1>Loading accounts...</h1>
        </div>
      </div>
    )
  }

  return (
    <div className="accounts">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>My Accounts</h1>
          </div>
          <button 
            onClick={() => setShowCreateForm(!showCreateForm)} 
            className="btn btn-primary"
          >
            {showCreateForm ? 'Cancel' : '+ Create New Account'}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Create Account Form */}
        {showCreateForm && (
          <div className="card mb-3">
            <h2>Create New Account</h2>
            <form onSubmit={handleCreateAccount}>
              <div className="form-group">
                <label>Account Type</label>
                <select
                  value={newAccount.account_type}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNewAccount({ ...newAccount, account_type: e.target.value as 'checking' | 'savings' })}
                  required
                >
                  <option value="checking">Checking</option>
                  <option value="savings">Savings</option>
                </select>
              </div>
              <div className="form-group">
                <label>Opening Balance</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={newAccount.opening_balance}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewAccount({ ...newAccount, opening_balance: e.target.value })}
                  placeholder="0.00"
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary">
                Create Account
              </button>
            </form>
          </div>
        )}

        {/* Account List */}
        {accounts.length === 0 ? (
          <div className="card text-center">
            <h2>No Accounts Yet</h2>
            <p>Create your first account to get started!</p>
          </div>
        ) : (
          <div className="grid grid-2">
            {accounts.map((account) => (
              <div key={account.id} className="card account-card">
                <div className="account-header">
                  <div>
                    <h3>{account.account_type.toUpperCase()}</h3>
                    <p className="text-muted">{account.account_number}</p>
                  </div>
                  <span className={`badge badge-${account.status.toLowerCase()}`}>
                    {account.status}
                  </span>
                </div>
                
                <div className="account-balance">
                  <span className="balance-label">Current Balance</span>
                  <span className="balance-amount">${account.balance.toFixed(2)}</span>
                </div>

                <div className="account-actions">
                  <button 
                    className="btn btn-sm btn-primary"
                    onClick={() => setSelectedAccount(selectedAccount === account.id ? null : account.id)}
                  >
                    {selectedAccount === account.id ? 'Hide' : 'Show'} Recent Transactions
                  </button>
                </div>

                {/* Recent Transactions */}
                {selectedAccount === account.id && (
                  <div className="recent-transactions">
                    <h4>Recent 5 Transactions</h4>
                    {recentTransactions[account.id]?.length > 0 ? (
                      <div className="transaction-list">
                        {recentTransactions[account.id].map((txn) => (
                          <div key={txn.transaction_id} className="transaction-item">
                            <div>
                              <strong>{txn.description || 'Transaction'}</strong>
                              <br />
                              <small className="text-muted">
                                {new Date(txn.created_at).toLocaleDateString()}
                              </small>
                            </div>
                            <div className={`transaction-amount ${txn.transaction_type}`}>
                              {txn.transaction_type === 'credit' ? '+' : '-'}
                              ${Math.abs(txn.amount).toFixed(2)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted">No transactions yet</p>
                    )}
                  </div>
                )}

                <div className="account-footer">
                  <small className="text-muted">
                    Created: {new Date(account.created_at).toLocaleDateString()}
                  </small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AccountsPage
