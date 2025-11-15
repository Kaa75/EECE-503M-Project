import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
      // Navigation is handled automatically by ProtectedRoute when user becomes null
    } catch (error) {
      console.error('Logout failed:', error)
    }
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

        {/* Quick Actions */}
        <h2>Quick Actions</h2>
        <div className="grid grid-2 mb-4">
          <Link to="/accounts" className="action-card card">
            <h3>💳 My Accounts</h3>
            <p>View and manage your bank accounts</p>
          </Link>

          <Link to="/transactions" className="action-card card">
            <h3>💸 Transactions</h3>
            <p>View transaction history and make transfers</p>
          </Link>

          <Link to="/support" className="action-card card">
            <h3>💬 Support</h3>
            <p>Create and manage support tickets</p>
          </Link>

          <Link to="/profile" className="action-card card">
            <h3>👤 Profile</h3>
            <p>Update your profile information</p>
          </Link>
        </div>

        {/* Admin/Auditor Actions */}
        {(user?.role === 'admin' || user?.role === 'auditor') && (
          <>
            <h2>Admin & Audit Tools</h2>
            <div className="grid grid-2">
              {user?.role === 'admin' && (
                <Link to="/admin" className="action-card card">
                  <h3>🔧 Admin Panel</h3>
                  <p>Manage users and system settings</p>
                </Link>
              )}
              
              {(user?.role === 'admin' || user?.role === 'auditor') && (
                <Link to="/audit" className="action-card card">
                  <h3>📊 Audit Logs</h3>
                  <p>View system audit logs and activities</p>
                </Link>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default DashboardPage
