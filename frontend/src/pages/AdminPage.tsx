import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import { User, UserRole } from '../types'
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
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [createForm, setCreateForm] = useState({
    username: '',
    full_name: '',
    email: '',
    phone: '',
    password: '',
    role: UserRole.CUSTOMER as string
  })
  const [showAccountsViewer, setShowAccountsViewer] = useState(false)
  const [accountsLoading, setAccountsLoading] = useState(false)
  const [viewAccountsUser, setViewAccountsUser] = useState<User | null>(null)
  const [userAccounts, setUserAccounts] = useState<any[]>([])

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
            <div className="mt-3">
              <button className="btn btn-primary" onClick={() => setShowCreateUser(true)}>
                + Create New User
              </button>
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
                            disabled={user.role === 'admin'}
                          >
                            {user.role === 'admin' ? 'Create Account (disabled)' : 'Create Account'}
                          </button>
                          <button
                            onClick={async () => {
                              setError(''); setSuccess('')
                              try {
                                await apiService.fetchCsrfToken()
                              } catch {}
                              setViewAccountsUser(user)
                              setShowAccountsViewer(true)
                              setAccountsLoading(true)
                              try {
                                const res = await apiService.getAdminUserAccounts(user.id)
                                setUserAccounts(res.accounts || [])
                              } catch (err: any) {
                                setError(err.message || 'Failed to load accounts')
                              } finally {
                                setAccountsLoading(false)
                              }
                            }}
                            className="btn btn-sm btn-secondary mr-1"
                          >
                            View Accounts
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

        {/* Accounts Viewer Modal */}
        {showAccountsViewer && viewAccountsUser && (
          <div className="modal-overlay" onClick={() => { setShowAccountsViewer(false); setUserAccounts([]); setViewAccountsUser(null) }}>
            <div className="modal-content" style={{ maxWidth: '800px' }} onClick={(e) => e.stopPropagation()}>
              <h3>Accounts for {viewAccountsUser.username}</h3>
              {accountsLoading ? <p>Loading accounts...</p> : userAccounts.length === 0 ? <p>No accounts found.</p> : (
                <div className="table-responsive" style={{ maxHeight: '320px', overflowY: 'auto' }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Number</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Balance</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userAccounts.map(acc => (
                        <tr key={acc.id}>
                          <td>{acc.id}</td>
                          <td>{acc.account_number}</td>
                          <td>{acc.account_type}</td>
                          <td>
                            <span className={`badge badge-${acc.status}`}>{acc.status}</span>
                          </td>
                          <td>${Number(acc.balance).toFixed(2)}</td>
                          <td>
                            {acc.status === 'active' && (
                              <button
                                className="btn btn-sm btn-warning mr-1"
                                onClick={async () => {
                                  setError(''); setSuccess('')
                                  try { await apiService.freezeAccount(acc.id); setSuccess('Account frozen');
                                    const res = await apiService.getAdminUserAccounts(viewAccountsUser.id); setUserAccounts(res.accounts || [])
                                  } catch (err: any) { setError(err.message || 'Freeze failed') }
                                }}
                              >Freeze</button>
                            )}
                            {acc.status === 'frozen' && (
                              <button
                                className="btn btn-sm btn-success mr-1"
                                onClick={async () => {
                                  setError(''); setSuccess('')
                                  try { await apiService.unfreezeAccount(acc.id); setSuccess('Account unfrozen');
                                    const res = await apiService.getAdminUserAccounts(viewAccountsUser.id); setUserAccounts(res.accounts || [])
                                  } catch (err: any) { setError(err.message || 'Unfreeze failed') }
                                }}
                              >Unfreeze</button>
                            )}
                            {acc.status !== 'closed' && (
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={async () => {
                                  if (!confirm('Close this account? This action is irreversible.')) return
                                  setError(''); setSuccess('')
                                  try { await apiService.closeAccount(acc.id); setSuccess('Account closed');
                                    const res = await apiService.getAdminUserAccounts(viewAccountsUser.id); setUserAccounts(res.accounts || [])
                                  } catch (err: any) { setError(err.message || 'Close failed') }
                                }}
                              >Close</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="flex-end mt-3">
                <button className="btn btn-secondary" onClick={() => { setShowAccountsViewer(false); setUserAccounts([]); setViewAccountsUser(null) }}>Close</button>
              </div>
            </div>
          </div>
        )}

        {/* Create User Modal */}
        {showCreateUser && (
          <div className="modal-overlay" onClick={() => setShowCreateUser(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h3>Create New User</h3>
              <form
                onSubmit={async (e) => {
                  e.preventDefault()
                  setError('')
                  setSuccess('')
                  try {
                    if (createForm.username.length < 3) throw new Error('Username too short')
                    if (createForm.password.length < 8) throw new Error('Password must be ≥ 8 chars')
                    if (createForm.full_name.length < 2) throw new Error('Full name too short')
                    await apiService.createUser({
                      username: createForm.username,
                      password: createForm.password,
                      email: createForm.email,
                      phone: createForm.phone,
                      full_name: createForm.full_name,
                      role: createForm.role
                    })
                    setSuccess('User created successfully')
                    setShowCreateUser(false)
                    setCreateForm({ username: '', full_name: '', email: '', phone: '', password: '', role: UserRole.CUSTOMER })
                    loadUsers()
                  } catch (err: any) {
                    setError(err.message || 'Failed to create user')
                  }
                }}
              >
                <div className="form-group">
                  <label>Username *</label>
                  <input
                    value={createForm.username}
                    onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                    required
                    minLength={3}
                  />
                </div>
                <div className="form-group">
                  <label>Full Name *</label>
                  <input
                    value={createForm.full_name}
                    onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                    required
                    minLength={2}
                  />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={createForm.email}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Phone *</label>
                  <input
                    value={createForm.phone}
                    onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Password *</label>
                  <input
                    type="password"
                    value={createForm.password}
                    onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                    required
                    minLength={8}
                  />
                </div>
                <div className="form-group">
                  <label>Role *</label>
                  <select
                    value={createForm.role}
                    onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  >
                    <option value={UserRole.CUSTOMER}>Customer</option>
                    <option value={UserRole.SUPPORT_AGENT}>Support Agent</option>
                    <option value={UserRole.AUDITOR}>Auditor</option>
                    <option value={UserRole.ADMIN}>Admin</option>
                  </select>
                </div>
                <div className="flex-end">
                  <button type="button" className="btn btn-secondary mr-2" onClick={() => setShowCreateUser(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Create User</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPage
