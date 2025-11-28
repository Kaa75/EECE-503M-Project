import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'

type UserAccount = {
  id: number
  account_number: string
  type: string
  balance: number
  status: string
}

type Biller = {
  id: string
  name: string
  account_number: string
  category?: string
}

type ScheduledPayment = {
  id: string
  billerId: string
  senderAccountId: number
  amount: number
  runAtISO: string
  description?: string
}

const STORAGE_KEYS = {
  billers: 'obs_billers',
  scheduled: 'obs_scheduled_payments',
}

const BillsPage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState<boolean>(true)
  const [accounts, setAccounts] = useState<UserAccount[]>([])
  const [csrfReady, setCsrfReady] = useState<boolean>(false)

  const [billers, setBillers] = useState<Biller[]>([])
  const [scheduled, setScheduled] = useState<ScheduledPayment[]>([])

  const [tab, setTab] = useState<'billers'|'pay'|'scheduled'|'history'>('billers')

  // Pay bill form state
  const [selectedBillerId, setSelectedBillerId] = useState<string>('')
  const [senderAccountId, setSenderAccountId] = useState<number | ''>('')
  const [amount, setAmount] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [customBillerAcc, setCustomBillerAcc] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')

  // History state
  const [historyAccountId, setHistoryAccountId] = useState<number | ''>('')
  const [history, setHistory] = useState<any[]>([])
  const [historyLoading, setHistoryLoading] = useState<boolean>(false)

  const selectedBiller = useMemo(() => billers.find(b => b.id === selectedBillerId), [billers, selectedBillerId])

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        // Load CSRF to enable mutating requests
        await apiService.fetchCsrfToken()
        setCsrfReady(true)
        // Load accounts via dashboard composite
        const dash = await apiService.getDashboard()
        const acctList = (dash.accounts || []).map((a: any) => ({
          id: a.id,
          account_number: a.account_number,
          type: a.account_type || a.type,
          balance: a.balance,
          status: a.status
        }))
        setAccounts(acctList)
        // Load billers & scheduled from localStorage
        const storedBillers = localStorage.getItem(STORAGE_KEYS.billers)
        const storedScheduled = localStorage.getItem(STORAGE_KEYS.scheduled)
        setBillers(storedBillers ? JSON.parse(storedBillers) : [])
        setScheduled(storedScheduled ? JSON.parse(storedScheduled) : [])
      } catch (e) {
        setError('Failed to initialize bills module')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const persistBillers = (next: Biller[]) => {
    setBillers(next)
    localStorage.setItem(STORAGE_KEYS.billers, JSON.stringify(next))
  }

  const persistScheduled = (next: ScheduledPayment[]) => {
    setScheduled(next)
    localStorage.setItem(STORAGE_KEYS.scheduled, JSON.stringify(next))
  }

  const addBiller = (name: string, account_number: string, category?: string) => {
    if (!name.trim() || !account_number.trim()) {
      setError('Biller name and account number are required')
      return
    }
    const id = `biller_${Date.now()}`
    const next = [...billers, { id, name: name.trim(), account_number: account_number.trim(), category }]
    persistBillers(next)
    setError('')
  }

  const removeBiller = (id: string) => {
    persistBillers(billers.filter(b => b.id !== id))
  }

  const schedulePayment = () => {
    setError('')
    setSuccess('')
    if (!selectedBillerId && !customBillerAcc.trim()) {
      setError('Select a biller or enter account number')
      return
    }
    if (!senderAccountId || typeof senderAccountId !== 'number') {
      setError('Select a sender account')
      return
    }
    const amt = parseFloat(amount)
    if (!amt || amt <= 0) {
      setError('Enter a valid positive amount')
      return
    }
    const runAt = new Date(Date.now() + 24 * 60 * 60 * 1000) // default: next day
    const sp: ScheduledPayment = {
      id: `sched_${Date.now()}`,
      billerId: selectedBillerId || 'custom',
      senderAccountId: senderAccountId,
      amount: amt,
      runAtISO: runAt.toISOString(),
      description: description || 'Scheduled bill payment'
    }
    persistScheduled([...scheduled, sp])
    setSuccess('Payment scheduled for next day')
  }

  const runScheduledNow = async (sp: ScheduledPayment) => {
    setError('')
    setSuccess('')
    try {
      const biller = billers.find(b => b.id === sp.billerId)
      const receiverAcc = biller ? biller.account_number : customBillerAcc
      if (!receiverAcc) {
        setError('Receiver account number missing')
        return
      }
      await apiService.externalTransfer({
        sender_account_id: sp.senderAccountId,
        receiver_account_number: receiverAcc,
        amount: sp.amount,
        description: sp.description || 'Bill payment'
      })
      // Remove from scheduled on success
      persistScheduled(scheduled.filter(s => s.id !== sp.id))
      setSuccess('Scheduled payment executed successfully')
    } catch (e: any) {
      const msg = e?.response?.data?.error || 'Payment failed'
      setError(msg)
    }
  }

  const payNow = async () => {
    setError('')
    setSuccess('')
    if (!csrfReady) {
      setError('Security token missing. Please retry.')
      return
    }
    if (!senderAccountId || typeof senderAccountId !== 'number') {
      setError('Select a sender account')
      return
    }
    const amt = parseFloat(amount)
    if (!amt || amt <= 0) {
      setError('Enter a valid positive amount')
      return
    }
    const receiverAcc = selectedBiller?.account_number || customBillerAcc.trim()
    if (!receiverAcc) {
      setError('Provide a biller account number')
      return
    }
    try {
      await apiService.externalTransfer({
        sender_account_id: senderAccountId,
        receiver_account_number: receiverAcc,
        amount: amt,
        description: description || `Bill payment to ${selectedBiller?.name || 'Biller'}`
      })
      setSuccess('Bill paid successfully')
      setAmount('')
      setDescription('')
      setCustomBillerAcc('')
    } catch (e: any) {
      const msg = e?.response?.data?.error || 'Payment failed'
      setError(msg)
    }
  }

  const loadHistory = async () => {
    if (!historyAccountId || typeof historyAccountId !== 'number') return
    setHistoryLoading(true)
    setError('')
    try {
      const res = await apiService.getAccountTransactions(historyAccountId, 50, 0)
      setHistory(res.transactions || [])
    } catch (e) {
      setError('Failed to load history')
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'history') {
      // default to first account
      if (accounts.length && !historyAccountId) {
        setHistoryAccountId(accounts[0].id)
      }
    }
  }, [tab, accounts, historyAccountId])

  useEffect(() => {
    if (tab === 'history' && historyAccountId) {
      loadHistory()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, historyAccountId])

  return (
    <div className="container">
      <button className="btn btn-secondary mb-2" onClick={() => navigate('/dashboard')}>← Back</button>
      <h1>Bills & Payments</h1>

      {error && <div className="alert alert-danger" role="alert">{error}</div>}
      {success && <div className="alert alert-success" role="alert">{success}</div>}

      {loading ? (
        <div className="card p-3">Loading bills module...</div>
      ) : (
        <div>
          <div className="btn-group mb-3" role="group" aria-label="Bills Tabs">
            <button className={`btn btn-${tab==='billers'?'primary':'outline-primary'}`} onClick={() => setTab('billers')}>Billers</button>
            <button className={`btn btn-${tab==='pay'?'primary':'outline-primary'}`} onClick={() => setTab('pay')}>Pay Bill</button>
            <button className={`btn btn-${tab==='scheduled'?'primary':'outline-primary'}`} onClick={() => setTab('scheduled')}>Scheduled</button>
            <button className={`btn btn-${tab==='history'?'primary':'outline-primary'}`} onClick={() => setTab('history')}>History</button>
          </div>

          {tab === 'billers' && (
            <div className="card p-3">
              <h3>Your Billers</h3>
              {billers.length === 0 ? (
                <p>No billers saved yet. Add one below.</p>
              ) : (
                <ul className="list-group mb-3">
                  {billers.map(b => (
                    <li key={b.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <div>
                        <strong>{b.name}</strong> {b.category ? `· ${b.category}` : ''}<br/>
                        <small>Acct: {b.account_number}</small>
                      </div>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => removeBiller(b.id)}>Remove</button>
                    </li>
                  ))}
                </ul>
              )}
              <h4>Add Biller</h4>
              <div className="row g-2">
                <div className="col-md-4">
                  <input className="form-control" placeholder="Biller name" id="billerName" />
                </div>
                <div className="col-md-4">
                  <input className="form-control" placeholder="Account number" id="billerAcc" />
                </div>
                <div className="col-md-3">
                  <input className="form-control" placeholder="Category (optional)" id="billerCat" />
                </div>
                <div className="col-md-1 d-grid">
                  <button className="btn btn-success" onClick={() => {
                    const nameEl = document.getElementById('billerName') as HTMLInputElement
                    const accEl = document.getElementById('billerAcc') as HTMLInputElement
                    const catEl = document.getElementById('billerCat') as HTMLInputElement
                    addBiller(nameEl.value, accEl.value, catEl.value)
                    nameEl.value = ''
                    accEl.value = ''
                    catEl.value = ''
                  }}>Add</button>
                </div>
              </div>
            </div>
          )}

          {tab === 'pay' && (
            <div className="card p-3">
              <h3>Pay a Bill</h3>
              <div className="row g-3">
                <div className="col-md-4">
                  <label className="form-label">Sender Account</label>
                  <select className="form-select" value={senderAccountId || ''} onChange={e => setSenderAccountId(Number(e.target.value))}>
                    <option value="">Select account</option>
                    {accounts.map(a => (
                      <option key={a.id} value={a.id}>{a.account_number} · {a.type} · Bal: {a.balance.toFixed(2)}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label">Biller</label>
                  <select className="form-select" value={selectedBillerId} onChange={e => setSelectedBillerId(e.target.value)}>
                    <option value="">Custom biller</option>
                    {billers.map(b => (
                      <option key={b.id} value={b.id}>{b.name} · {b.account_number}</option>
                    ))}
                  </select>
                </div>
                {!selectedBiller && (
                  <div className="col-md-4">
                    <label className="form-label">Receiver Account Number</label>
                    <input className="form-control" value={customBillerAcc} onChange={e => setCustomBillerAcc(e.target.value)} placeholder="e.g., ACC-XXXXXXXX" />
                  </div>
                )}
                <div className="col-md-3">
                  <label className="form-label">Amount</label>
                  <input className="form-control" type="number" step="0.01" min="0" value={amount} onChange={e => setAmount(e.target.value)} />
                </div>
                <div className="col-md-9">
                  <label className="form-label">Description (optional)</label>
                  <input className="form-control" value={description} onChange={e => setDescription(e.target.value)} placeholder="e.g., Electricity bill Nov" />
                </div>
                <div className="col-md-12 d-flex gap-2">
                  <button className="btn btn-primary" onClick={payNow}>Pay Now</button>
                  <button className="btn btn-outline-primary" onClick={schedulePayment}>Schedule (next day)</button>
                </div>
              </div>
            </div>
          )}

          {tab === 'scheduled' && (
            <div className="card p-3">
              <h3>Scheduled Payments</h3>
              {scheduled.length === 0 ? (
                <p>No scheduled payments.</p>
              ) : (
                <ul className="list-group">
                  {scheduled.map(sp => (
                    <li key={sp.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <div>
                        <strong>{billers.find(b => b.id === sp.billerId)?.name || 'Custom biller'}</strong>
                        <div><small>Run at: {new Date(sp.runAtISO).toLocaleString()}</small></div>
                        <div><small>Amount: {sp.amount.toFixed(2)} · Sender ID: {sp.senderAccountId}</small></div>
                      </div>
                      <div className="d-flex gap-2">
                        <button className="btn btn-sm btn-outline-success" onClick={() => runScheduledNow(sp)}>Run Now</button>
                        <button className="btn btn-sm btn-outline-danger" onClick={() => persistScheduled(scheduled.filter(s => s.id !== sp.id))}>Cancel</button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {tab === 'history' && (
            <div className="card p-3">
              <h3>Bill Payment History</h3>
              <div className="row g-2 mb-2">
                <div className="col-md-6">
                  <label className="form-label">Account</label>
                  <select className="form-select" value={historyAccountId || ''} onChange={e => setHistoryAccountId(Number(e.target.value))}>
                    <option value="">Select account</option>
                    {accounts.map(a => (
                      <option key={a.id} value={a.id}>{a.account_number} · {a.type}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-6 d-flex align-items-end">
                  <button className="btn btn-outline-secondary" onClick={loadHistory} disabled={historyLoading || !historyAccountId}>
                    {historyLoading ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
              </div>
              {history.length === 0 ? (
                <p>No transactions found.</p>
              ) : (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Description</th>
                        <th>Receiver</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((t: any) => (
                        <tr key={t.transaction_id}>
                          <td>{new Date(t.created_at).toLocaleString()}</td>
                          <td>{t.transaction_type}</td>
                          <td>{Number(t.amount).toFixed(2)}</td>
                          <td>{t.description}</td>
                          <td>{t.receiver_account}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default BillsPage
