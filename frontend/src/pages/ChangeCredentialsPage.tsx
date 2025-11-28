import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'

const ChangeCredentialsPage: React.FC = () => {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await apiService.changeCredentials({
        current_password: currentPassword,
        new_username: newUsername,
        new_password: newPassword
      })
      if (res.success) {
        navigate('/dashboard')
      } else {
        setError('Failed to change credentials')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card card">
        <h2>Change Credentials</h2>
        <p>Please update your username and password before continuing.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="current_password">Current Password</label>
            <input
              id="current_password"
              type="password"
              value={currentPassword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="new_username">New Username</label>
            <input
              id="new_username"
              type="text"
              value={newUsername}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewUsername(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="new_password">New Password</label>
            <input
              id="new_password"
              type="password"
              value={newPassword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save and Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChangeCredentialsPage
