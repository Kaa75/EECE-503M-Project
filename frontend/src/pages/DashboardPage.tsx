import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'
import apiService from '../services/api'
import { DashboardResponse, UserRole } from '../types'
import CreateAccountModal from '../components/CreateAccountModal'

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false)

  useEffect(() => {
    const loadDashboard = async () => {
      if (!user) return
      try {
        setLoading(true)
        setError('')
        const data = await apiService.getDashboard()
        setDashboard(data as DashboardResponse)
      } catch (e: any) {
        // Suppress generic permission error banner for roles without dashboard aggregate access
        if (e.message && /permission|forbidden|unauthorized/i.test(e.message)) {
          setError('')
        } else {
          setError(e.message || 'Failed to load dashboard')
        }
      } finally {
        setLoading(false)
      }
    }
    loadDashboard()
  }, [user])

  const handleLogout = async () => {
    try {
      await logout()
      // Navigation is handled automatically by ProtectedRoute when user becomes null
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <div className="container">
          <h1>Loading dashboard...</h1>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="container">
        {/* Header */}
        <div className="dashboard-header">
          <div>
            <h1>Dashboard</h1>
            <p className="text-muted">Welcome back, {user?.full_name || user?.username}!</p>
          </div>
          <button onClick={handleLogout} className="btn btn-outline">
            Logout
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* User Info Card */}
        <div className="card mb-3">
          <h2>Account Information</h2>
          <div className="user-info">
            <div>
              <strong>Username:</strong> {user?.username}
            </div>
            <div>
              <strong>Email:</strong> {user?.email}
            </div>
            <div>
              <strong>Phone:</strong> {user?.phone}
            </div>
            <div>
              <strong>Role:</strong> <span className="badge">{user?.role}</span>
            </div>
          </div>
        </div>

        {/* Quick Actions (from backend) */}
        <h2>Quick Actions</h2>
        <div className="grid grid-2 mb-4">
          {dashboard?.quick_links
            .filter(link => {
              // Hide support link entirely for auditor
              if (user?.role === UserRole.AUDITOR && link.path === '/support') return false
              // Admin: hide Internal/External Transfer cards, and Bills, but keep View All Transactions
              if (user?.role === UserRole.ADMIN) {
                const label = (link.label || '').toLowerCase()
                if (label.includes('internal transfer') || label.includes('external transfer')) return false
                if (link.path === '/bills') return false
              }
              return true
            })
            .map(link => (
              <Link key={link.path} to={link.path} className="action-card card">
                <h3>{link.label}</h3>
                <p>Go to {link.label}</p>
              </Link>
            ))}
          {user?.role !== UserRole.AUDITOR && user?.role !== UserRole.ADMIN && (
            <Link to="/support" className="action-card card">
              <h3>💬 Support</h3>
              <p>Create and manage support tickets</p>
            </Link>
          )}
          <Link to="/profile" className="action-card card">
            <h3>👤 Profile</h3>
            <p>Update your profile information</p>
          </Link>
        </div>

        {/* Accounts + Recent Transactions (admins should not have personal accounts) */}
        {user?.role === UserRole.CUSTOMER ? (
          <>
            <div className="flex-between mb-2">
              <h2>My Accounts</h2>
              {dashboard && dashboard.accounts.length > 0 && (
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                  + New Account
                </button>
              )}
            </div>
            {(!dashboard || dashboard.accounts.length === 0) && (
              <div className="card mb-3">
                <p>No accounts yet. Create one to get started.</p>
                <button className="btn btn-primary mt-2" onClick={() => setShowCreateModal(true)}>
                  Create Account
                </button>
              </div>
            )}
            <div className="grid grid-2">
              {dashboard?.accounts.map(acc => (
                <div key={acc.id} className="card account-card">
                  <div className="account-header">
                    <div>
                      <h3>{acc.account_type.toUpperCase()}</h3>
                      <p className="text-muted">{acc.account_number}</p>
                    </div>
                    <span className={`badge badge-${acc.status}`}>{acc.status}</span>
                  </div>
                  <div className="account-balance">
                    <span className="balance-label">Balance</span>
                    <span className="balance-amount">${acc.balance.toFixed(2)}</span>
                  </div>
                  <div className="recent-transactions">
                    <h4>Recent Transactions</h4>
                    {acc.recent_transactions.length > 0 ? (
                      <div className="transaction-list">
                        {acc.recent_transactions.map(txn => (
                          <div key={txn.transaction_id} className="transaction-item">
                            <div>
                              <strong>{txn.description || 'Transaction'}</strong><br />
                              <small className="text-muted">{new Date(txn.created_at).toLocaleDateString()}</small>
                            </div>
                            <div className={`transaction-amount ${txn.transaction_type}`}>
                              {txn.transaction_type === 'credit' ? '+' : '-'}${Math.abs(txn.amount).toFixed(2)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted">No recent transactions</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : null}

        {/* Admin/Auditor Actions */}
        {(user?.role === UserRole.ADMIN || user?.role === UserRole.AUDITOR) && (
          <>
            <h2>Admin & Audit Tools</h2>
            <div className="grid grid-2">
              {user?.role === UserRole.ADMIN && (
                <Link to="/admin" className="action-card card">
                  <h3>🔧 Admin Panel</h3>
                  <p>Manage users and system settings</p>
                </Link>
              )}
              
              {(user?.role === UserRole.ADMIN || user?.role === UserRole.AUDITOR) && (
                <Link to="/audit" className="action-card card">
                  <h3>📊 Audit Logs</h3>
                  <p>View system audit logs and activities</p>
                </Link>
              )}
            </div>
          </>
        )}

        {/* Create Account Modal */}
        {showCreateModal && (
          <CreateAccountModal
            onClose={() => setShowCreateModal(false)}
            onCreated={(newAccount) => {
              // Refresh: simplest is to reload dashboard
              setShowCreateModal(false)
              ;(async () => {
                try {
                  setLoading(true)
                  const data = await apiService.getDashboard()
                  setDashboard(data as DashboardResponse)
                } catch (e: any) {
                  setError(e.message || 'Failed to refresh dashboard')
                } finally {
                  setLoading(false)
                }
              })()
            }}
          />
        )}
      </div>
    </div>
  )
}

export default DashboardPage
