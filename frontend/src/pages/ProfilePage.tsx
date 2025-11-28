import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'

const ProfilePage: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [profile, setProfile] = useState({
    email: user?.email || '',
    phone: user?.phone || '',
    full_name: user?.full_name || ''
  })

  const [password, setPassword] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  })

  const handleUpdateProfile = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      await apiService.updateProfile(profile)
      setSuccess('Profile updated successfully!')
      setEditing(false)
      window.location.reload()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update profile'
      setError(message)
    }
  }

  const handleChangePassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (password.new_password !== password.confirm_password) {
      setError('New passwords do not match')
      return
    }

    if (password.new_password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    try {
      await apiService.changePassword({
        old_password: password.old_password,
        new_password: password.new_password
      })
      setSuccess('Password changed successfully!')
      setChangingPassword(false)
      setPassword({ old_password: '', new_password: '', confirm_password: '' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to change password'
      setError(message)
    }
  }

  return (
    <div className="profile">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>My Profile</h1>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Auditor Warning */}
        {user?.role === 'auditor' && (
          <div className="alert alert-warning mb-3">
            <strong>Note:</strong> As an auditor, your profile is read-only for security and compliance purposes. 
            You cannot modify your profile or change your password.
          </div>
        )}

        <div className="card mb-3">
          <div className="flex-between mb-2">
            <h2>Profile Information</h2>
            {!editing && user?.role !== 'auditor' && (
              <button onClick={() => setEditing(true)} className="btn btn-outline">
                Edit Profile
              </button>
            )}
          </div>

          {editing ? (
            <form onSubmit={handleUpdateProfile}>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setProfile({ ...profile, full_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setProfile({ ...profile, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={profile.phone}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setProfile({ ...profile, phone: e.target.value })}
                  required
                />
              </div>

              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary">
                  Save Changes
                </button>
                <button 
                  type="button" 
                  onClick={() => setEditing(false)} 
                  className="btn btn-outline"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="user-info">
              <div><strong>Username:</strong> {user?.username}</div>
              <div><strong>Full Name:</strong> {user?.full_name}</div>
              <div><strong>Email:</strong> {user?.email}</div>
              <div><strong>Phone:</strong> {user?.phone}</div>
              <div><strong>Role:</strong> <span className="badge">{user?.role}</span></div>
            </div>
          )}
        </div>

        {/* Change Password Section - Hidden for Auditors */}
        {user?.role !== 'auditor' && (
          <div className="card">
            <div className="flex-between mb-2">
              <h2>Change Password</h2>
              {!changingPassword && (
                <button onClick={() => setChangingPassword(true)} className="btn btn-outline">
                  Change Password
                </button>
              )}
            </div>

          {changingPassword ? (
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label>Current Password</label>
                <input
                  type="password"
                  value={password.old_password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword({ ...password, old_password: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={password.new_password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword({ ...password, new_password: e.target.value })}
                  placeholder="At least 8 characters"
                  required
                />
              </div>

              <div className="form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  value={password.confirm_password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword({ ...password, confirm_password: e.target.value })}
                  required
                />
              </div>

              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary">
                  Update Password
                </button>
                <button 
                  type="button" 
                  onClick={() => {
                    setChangingPassword(false)
                    setPassword({ old_password: '', new_password: '', confirm_password: '' })
                  }} 
                  className="btn btn-outline"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <p className="text-muted">
              Keep your account secure by using a strong, unique password.
            </p>
          )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProfilePage
