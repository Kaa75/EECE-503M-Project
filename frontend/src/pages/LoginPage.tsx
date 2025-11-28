import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login, error: authError, clearError, isLoading } = useAuth()

  // Sync local error with auth context error
  useEffect(() => {
    if (authError) {
      setError(authError)
    }
  }, [authError])

  // Clear errors when component unmounts or user navigates away
  useEffect(() => {
    return () => {
      clearError()
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    clearError()
    setLoading(true)

    console.log('Login form submitted with:', { username, password: '***' });

    try {
      const mustChange = await login(username, password)
      console.log('Login successful, mustChange:', mustChange);
      if (mustChange) {
        navigate('/change-credentials')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Login error in LoginPage:', err);
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      console.log('Setting error message:', errorMessage);
      setError(errorMessage)
      // Don't set loading to false immediately to ensure error is displayed
    } finally {
      console.log('Setting loading to false');
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card card">
        <h1>Online Banking System</h1>
        <h2>Login</h2>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setUsername(e.target.value)
                setError('')
                clearError()
              }}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setPassword(e.target.value)
                setError('')
                clearError()
              }}
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading || isLoading}>
            {(loading || isLoading) ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="mt-3">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
