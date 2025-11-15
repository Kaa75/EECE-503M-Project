import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import apiService from '../services/api'
import { SupportTicket, CreateTicketRequest } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'

const SupportPage: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [tickets, setTickets] = useState<SupportTicket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // Create ticket form
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [ticketForm, setTicketForm] = useState<CreateTicketRequest>({
    subject: '',
    description: '',
    priority: 'medium'
  })
  
  // Note form
  const [noteText, setNoteText] = useState('')
  const [addingNote, setAddingNote] = useState(false)
  
  // Status filter
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'in_progress' | 'resolved'>('all')

  const isSupportAgent = user?.role === 'support_agent' || user?.role === 'admin'

  useEffect(() => {
    loadTickets()
  }, [statusFilter])

  const loadTickets = async () => {
    try {
      setLoading(true)
      setError(null)
      
      if (isSupportAgent) {
        // Support agents see all open tickets
        const response = await apiService.getOpenTickets(50, 0)
        setTickets(response.tickets)
      } else {
        // Customers see their own tickets
        const response = await apiService.getCustomerTickets(user!.id, 50, 0)
        setTickets(response.tickets)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tickets')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setError(null)
      setSuccess(null)
      
      await apiService.createTicket(ticketForm)
      
      setSuccess('Ticket created successfully')
      setShowCreateModal(false)
      setTicketForm({ subject: '', description: '', priority: 'medium' })
      loadTickets()
    } catch (err: any) {
      setError(err.message || 'Failed to create ticket')
    }
  }

  const handleViewTicket = async (ticketId: string) => {
    try {
      setError(null)
      const ticket = await apiService.getTicket(ticketId)
      setSelectedTicket(ticket)
    } catch (err: any) {
      setError(err.message || 'Failed to load ticket details')
    }
  }

  const handleUpdateStatus = async (ticketId: string, status: 'open' | 'in_progress' | 'resolved') => {
    try {
      setError(null)
      setSuccess(null)
      
      await apiService.updateTicketStatus(ticketId, { status })
      
      setSuccess(`Ticket status updated to ${status.replace('_', ' ')}`)
      
      // Reload ticket details
      if (selectedTicket) {
        handleViewTicket(ticketId)
      }
      loadTickets()
    } catch (err: any) {
      setError(err.message || 'Failed to update ticket status')
    }
  }

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !noteText.trim()) return
    
    try {
      setError(null)
      setSuccess(null)
      setAddingNote(true)
      
      await apiService.addNote(selectedTicket.ticket_id, { note: noteText })
      
      setSuccess('Note added successfully')
      setNoteText('')
      
      // Reload ticket details
      handleViewTicket(selectedTicket.ticket_id)
    } catch (err: any) {
      setError(err.message || 'Failed to add note')
    } finally {
      setAddingNote(false)
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'open':
        return 'badge-danger'
      case 'in_progress':
        return 'badge-warning'
      case 'resolved':
        return 'badge-success'
      default:
        return 'badge-secondary'
    }
  }

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'badge-danger'
      case 'medium':
        return 'badge-warning'
      case 'low':
        return 'badge-info'
      default:
        return 'badge-secondary'
    }
  }

  const filteredTickets = tickets.filter(ticket => {
    if (statusFilter === 'all') return true
    return ticket.status === statusFilter
  })

  if (loading) return <LoadingSpinner />
  
  return (
    <div className="support">
      <div className="container">
        <div className="flex-between mb-3">
          <div className="flex-start">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary mr-2">
              ← Back to Dashboard
            </button>
            <h1>Support Tickets</h1>
          </div>
          {!isSupportAgent && (
            <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
              Create Ticket
            </button>
          )}
        </div>

        {error && <div className="alert alert-error mb-3">{error}</div>}
        {success && <div className="alert alert-success mb-3">{success}</div>}

        {/* Ticket List */}
        {!selectedTicket && (
          <div className="card">
            <div className="flex-between mb-3">
              <h2>{isSupportAgent ? 'All Open Tickets' : 'My Tickets'}</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`btn ${statusFilter === 'all' ? 'btn-primary' : 'btn-outline'}`}
                >
                  All
                </button>
                <button
                  onClick={() => setStatusFilter('open')}
                  className={`btn ${statusFilter === 'open' ? 'btn-primary' : 'btn-outline'}`}
                >
                  Open
                </button>
                <button
                  onClick={() => setStatusFilter('in_progress')}
                  className={`btn ${statusFilter === 'in_progress' ? 'btn-primary' : 'btn-outline'}`}
                >
                  In Progress
                </button>
                <button
                  onClick={() => setStatusFilter('resolved')}
                  className={`btn ${statusFilter === 'resolved' ? 'btn-primary' : 'btn-outline'}`}
                >
                  Resolved
                </button>
              </div>
            </div>

            {filteredTickets.length === 0 ? (
              <p className="text-muted">No tickets found.</p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>Subject</th>
                      {isSupportAgent && <th>Customer</th>}
                      <th>Status</th>
                      <th>Priority</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTickets.map(ticket => (
                      <tr key={ticket.ticket_id}>
                        <td><code>{ticket.ticket_id.substring(0, 8)}</code></td>
                        <td>{ticket.subject}</td>
                        {isSupportAgent && <td>{ticket.customer_name || `User ${ticket.customer_id}`}</td>}
                        <td>
                          <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                            {ticket.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${getPriorityBadgeClass(ticket.priority)}`}>
                            {ticket.priority}
                          </span>
                        </td>
                        <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            onClick={() => handleViewTicket(ticket.ticket_id)}
                            className="btn btn-sm btn-primary"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Ticket Details */}
        {selectedTicket && (
          <div>
            <button
              onClick={() => setSelectedTicket(null)}
              className="btn btn-outline mb-3"
            >
              ← Back to Tickets
            </button>

            <div className="card mb-3">
              <div className="flex-between mb-2">
                <h2>Ticket Details</h2>
                <div className="flex gap-2">
                  <span className={`badge ${getStatusBadgeClass(selectedTicket.status)}`}>
                    {selectedTicket.status.replace('_', ' ')}
                  </span>
                  <span className={`badge ${getPriorityBadgeClass(selectedTicket.priority)}`}>
                    {selectedTicket.priority}
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <p><strong>Ticket ID:</strong> <code>{selectedTicket.ticket_id}</code></p>
                <p><strong>Subject:</strong> {selectedTicket.subject}</p>
                <p><strong>Customer:</strong> {selectedTicket.customer_name || `User ${selectedTicket.customer_id}`}</p>
                {selectedTicket.assigned_agent_name && (
                  <p><strong>Assigned Agent:</strong> {selectedTicket.assigned_agent_name}</p>
                )}
                <p><strong>Created:</strong> {new Date(selectedTicket.created_at).toLocaleString()}</p>
                <p><strong>Last Updated:</strong> {new Date(selectedTicket.updated_at).toLocaleString()}</p>
              </div>

              <div className="mb-3">
                <h3>Description</h3>
                <p className="text-muted">{selectedTicket.description}</p>
              </div>

              {/* Status Update - Support Agents Only */}
              {isSupportAgent && (
                <div className="mb-3">
                  <h3>Update Status</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleUpdateStatus(selectedTicket.ticket_id, 'open')}
                      className="btn btn-outline"
                      disabled={selectedTicket.status === 'open'}
                    >
                      Open
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(selectedTicket.ticket_id, 'in_progress')}
                      className="btn btn-outline"
                      disabled={selectedTicket.status === 'in_progress'}
                    >
                      In Progress
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(selectedTicket.ticket_id, 'resolved')}
                      className="btn btn-outline"
                      disabled={selectedTicket.status === 'resolved'}
                    >
                      Resolved
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Notes Section */}
            <div className="card">
              <h3 className="mb-3">Communication</h3>
              
              {/* Add Note Form */}
              <form onSubmit={handleAddNote} className="mb-3">
                <div className="form-group">
                  <label>Add Note</label>
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Type your message here..."
                    rows={4}
                    required
                  />
                </div>
                <button type="submit" className="btn btn-primary" disabled={addingNote}>
                  {addingNote ? 'Adding...' : 'Add Note'}
                </button>
              </form>

              {/* Notes List */}
              <div className="notes-list">
                <h4 className="mb-2">Notes ({selectedTicket.notes?.length || 0})</h4>
                {(!selectedTicket.notes || selectedTicket.notes.length === 0) ? (
                  <p className="text-muted">No notes yet.</p>
                ) : (
                  <div className="space-y-2">
                    {selectedTicket.notes.map(note => (
                      <div key={note.note_id} className="note-item p-3 mb-2" style={{ 
                        backgroundColor: '#f8f9fa', 
                        borderRadius: '8px',
                        border: '1px solid #dee2e6'
                      }}>
                        <div className="flex-between mb-1">
                          <strong>{note.user_name}</strong>
                          <span className="text-muted" style={{ fontSize: '0.875rem' }}>
                            {new Date(note.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="mb-0">{note.note}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Create Ticket Modal */}
        {showCreateModal && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Create Support Ticket</h2>
              <form onSubmit={handleCreateTicket}>
                <div className="form-group">
                  <label>Subject *</label>
                  <input
                    type="text"
                    value={ticketForm.subject}
                    onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })}
                    placeholder="Brief description of your issue"
                    required
                    minLength={5}
                  />
                </div>

                <div className="form-group">
                  <label>Priority</label>
                  <select
                    value={ticketForm.priority}
                    onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Description *</label>
                  <textarea
                    value={ticketForm.description}
                    onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                    placeholder="Detailed description of your issue"
                    rows={5}
                    required
                    minLength={10}
                  />
                </div>

                <div className="flex gap-2">
                  <button type="submit" className="btn btn-primary">
                    Create Ticket
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn btn-outline"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SupportPage
