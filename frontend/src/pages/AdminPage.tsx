import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import { User } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'

const AdminPage: React.FC = () => {
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [newRole, setNewRole] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [showAccountModal, setShowAccountModal] = useState(false)
  const [accountForm, setAccountForm] = useState({
    userId: 0,
    accountType: 'checking' as 'checking' | 'savings',
    openingBalance: 0
  })

  useEffect(() => {
    loadUsers()
  }, [roleFilter])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError('')
      
      let data
      if (roleFilter === 'all') {
        data = await apiService.getAllUsers(100, 0)
      } else {
        data = await apiService.getUsersByRole(roleFilter, 100, 0)
      }
      
      setUsers(data.users)
    } catch (err: any) {
      setError(err.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      setError('')
      setSuccess('')
      await apiService.assignRole(userId, role)
      setSuccess(`Role updated to ${role} successfully`)
      setSelectedUser(null)
      setNewRole('')
      loadUsers()
    } catch (err: any) {
      setError(err.message || 'Failed to update role')
    }
  }

  const handleDeactivate = async (userId: number) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return
    
    try {
      setError('')
      setSuccess('')
      await apiService.deactivateUser(userId)
      setSuccess('User deactivated successfully')
      loadUsers()
    } catch (err: any) {
      setError(err.message || 'Failed to deactivate user')
    }
  }

  const handleActivate = async (userId: number) => {
    try {
      setError('')
      setSuccess('')
      await apiService.activateUser(userId)
      setSuccess('User activated successfully')
      loadUsers()
    } catch (err: any) {
      setError(err.message || 'Failed to activate user')
    }
  }

  const handleCreateAccount = async () => {
    try {
      setError('')
      setSuccess('')
      await apiService.createAccountForUser(
        accountForm.userId,
        accountForm.accountType,
        accountForm.openingBalance
      )
      setSuccess(`${accountForm.accountType} account created successfully for user`)
      setShowAccountModal(false)
      setAccountForm({ userId: 0, accountType: 'checking', openingBalance: 0 })
    } catch (err: any) {
      setError(err.message || 'Failed to create account')
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div className="admin">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>Admin Panel</h1>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Filters */}
        <div className="card mb-3">
          <div className="card-body">
            <h3>Filter Users</h3>
            <div className="form-group">
              <label>Role:</label>
              <select 
                value={roleFilter} 
                onChange={(e) => setRoleFilter(e.target.value)}
                className="form-control"
              >
                <option value="all">All Users</option>
                <option value="customer">Customers</option>
                <option value="support_agent">Support Agents</option>
                <option value="auditor">Auditors</option>
                <option value="admin">Admins</option>
              </select>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="card">
          <div className="card-body">
            <h3>Users ({users.length})</h3>
            {users.length === 0 ? (
              <p>No users found.</p>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Username</th>
                      <th>Full Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.username}</td>
                        <td>{user.full_name}</td>
                        <td>{user.email}</td>
                        <td>
                          <span className={`badge badge-${user.role === 'admin' ? 'danger' : user.role === 'support_agent' ? 'warning' : user.role === 'auditor' ? 'info' : 'info'}`}>
                            {user.role === 'support_agent' ? 'Support Agent' : user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                          </span>
                        </td>
                        <td>
                          <span className={`badge badge-${user.is_active ? 'success' : 'secondary'}`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>{new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            onClick={() => {
                              setSelectedUser(user)
                              setNewRole(user.role)
                            }}
                            className="btn btn-sm btn-primary mr-1"
                          >
                            Change Role
                          </button>
                          <button
                            onClick={() => {
                              setAccountForm({ userId: user.id, accountType: 'checking', openingBalance: 0 })
                              setShowAccountModal(true)
                            }}
                            className="btn btn-sm btn-info mr-1"
                          >
                            Create Account
                          </button>
                          {user.is_active ? (
                            <button
                              onClick={() => handleDeactivate(user.id)}
                              className="btn btn-sm btn-danger"
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              onClick={() => handleActivate(user.id)}
                              className="btn btn-sm btn-success"
                            >
                              Activate
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Role Change Modal */}
        {selectedUser && (
          <div className="modal-overlay" onClick={() => setSelectedUser(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h3>Change Role for {selectedUser.username}</h3>
              <div className="form-group">
                <label>New Role:</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="form-control"
                >
                  <option value="customer">Customer</option>
                  <option value="support_agent">Support Agent</option>
                  <option value="auditor">Auditor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex-end">
                <button
                  onClick={() => setSelectedUser(null)}
                  className="btn btn-secondary mr-2"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleRoleChange(selectedUser.id, newRole)}
                  className="btn btn-primary"
                >
                  Update Role
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Account Modal */}
        {showAccountModal && (
          <div className="modal-overlay" onClick={() => setShowAccountModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h3>Create Account for User ID: {accountForm.userId}</h3>
              <div className="form-group">
                <label>Account Type:</label>
                <select
                  value={accountForm.accountType}
                  onChange={(e) => setAccountForm({ ...accountForm, accountType: e.target.value as 'checking' | 'savings' })}
                  className="form-control"
                >
                  <option value="checking">Checking</option>
                  <option value="savings">Savings</option>
                </select>
              </div>
              <div className="form-group">
                <label>Opening Balance:</label>
                <input
                  type="number"
                  value={accountForm.openingBalance}
                  onChange={(e) => setAccountForm({ ...accountForm, openingBalance: parseFloat(e.target.value) || 0 })}
                  className="form-control"
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="flex-end">
                <button
                  onClick={() => setShowAccountModal(false)}
                  className="btn btn-secondary mr-2"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateAccount}
                  className="btn btn-primary"
                >
                  Create Account
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPage
