import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import { AuditLog } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'

const AuditPage: React.FC = () => {
  const navigate = useNavigate()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'login' | 'suspicious' | 'admin' | 'freeze'>('all')
  const [totalCount, setTotalCount] = useState(0)
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  useEffect(() => {
    loadLogs()
  }, [filter, offset])

  const loadLogs = async () => {
    try {
      setLoading(true)
      setError('')
      
      let data
      switch (filter) {
        case 'login':
          data = await apiService.getLoginAttempts(undefined, limit, offset)
          break
        case 'suspicious':
          data = await apiService.getSuspiciousActivities(limit, offset)
          break
        case 'admin':
          data = await apiService.getAdminActions(limit, offset)
          break
        case 'freeze':
          data = await apiService.getAccountFreezeLogs(limit, offset)
          break
        default:
          data = await apiService.getAuditLogs({ limit, offset })
      }
      
      setLogs(data.logs)
      setTotalCount(data.total_count)
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  const getActionBadgeClass = (action: string) => {
    const actionLower = action.toLowerCase()
    if (actionLower.includes('login') || actionLower.includes('register')) return 'badge-info'
    if (actionLower.includes('transfer') || actionLower.includes('create')) return 'badge-success'
    if (actionLower.includes('freeze') || actionLower.includes('deactivate')) return 'badge-danger'
    if (actionLower.includes('role') || actionLower.includes('update')) return 'badge-warning'
    return 'badge-secondary'
  }

  const handlePrevPage = () => {
    if (offset > 0) {
      setOffset(Math.max(0, offset - limit))
    }
  }

  const handleNextPage = () => {
    if (offset + limit < totalCount) {
      setOffset(offset + limit)
    }
  }

  if (loading && logs.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="audit">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>Audit Logs</h1>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Filters */}
        <div className="card mb-3">
          <div className="card-body">
            <h3>Filter Logs</h3>
            <div className="form-group">
              <label>Log Type:</label>
              <select 
                value={filter} 
                onChange={(e) => {
                  setFilter(e.target.value as any)
                  setOffset(0)
                }}
                className="form-control"
              >
                <option value="all">All Logs</option>
                <option value="login">Login Attempts</option>
                <option value="suspicious">Suspicious Activities</option>
                <option value="admin">Admin Actions</option>
                <option value="freeze">Account Freeze Logs</option>
              </select>
            </div>
          </div>
        </div>

        {/* Logs Table */}
        <div className="card">
          <div className="card-body">
            <h3>
              Audit Logs ({totalCount} total)
              {loading && <span className="ml-2">Loading...</span>}
            </h3>
            
            {logs.length === 0 ? (
              <p>No audit logs found.</p>
            ) : (
              <>
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>User ID</th>
                        <th>Action</th>
                        <th>Resource</th>
                        <th>Details</th>
                        <th>IP Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.id}>
                          <td>{new Date(log.timestamp).toLocaleString()}</td>
                          <td>{log.user_id || 'N/A'}</td>
                          <td>
                            <span className={`badge ${getActionBadgeClass(log.action)}`}>
                              {log.action}
                            </span>
                          </td>
                          <td>
                            {log.resource_type && (
                              <span>
                                {log.resource_type}
                                {log.resource_id && ` (${log.resource_id})`}
                              </span>
                            )}
                          </td>
                          <td>
                            <small>{log.details || 'N/A'}</small>
                          </td>
                          <td>
                            <small>{log.ip_address || 'N/A'}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="flex-between mt-3">
                  <div>
                    Showing {offset + 1} - {Math.min(offset + limit, totalCount)} of {totalCount}
                  </div>
                  <div>
                    <button
                      onClick={handlePrevPage}
                      disabled={offset === 0}
                      className="btn btn-secondary mr-2"
                    >
                      Previous
                    </button>
                    <button
                      onClick={handleNextPage}
                      disabled={offset + limit >= totalCount}
                      className="btn btn-secondary"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuditPage
