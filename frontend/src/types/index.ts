export enum UserRole {
  CUSTOMER = 'customer',
  SUPPORT_AGENT = 'support_agent',
  AUDITOR = 'auditor',
  ADMIN = 'admin'
}

export interface User {
  id: number
  username: string
  email: string
  phone: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface Account {
  id: number
  account_number: string
  user_id: number
  account_type: 'checking' | 'savings'
  balance: number
  status: 'active' | 'frozen' | 'closed'
  opening_balance: number
  created_at: string
}

export interface Transaction {
  id: number
  transaction_id: string
  sender_id: number
  sender_account_id: number
  receiver_account_id: number
  amount: number
  transaction_type: 'credit' | 'debit'
  description?: string
  created_at: string
}

export interface TicketNote {
  note_id: number
  user_id: number
  user_name: string
  note: string
  created_at: string
}

export interface SupportTicket {
  id: number
  ticket_id: string
  customer_id: number
  customer_name?: string
  assigned_agent_id?: number
  assigned_agent_name?: string
  subject: string
  description: string
  status: 'open' | 'in_progress' | 'resolved'
  priority: string
  created_at: string
  updated_at: string
  resolved_at?: string
  notes?: TicketNote[]
}

export interface AuditLog {
  id: number
  user_id: number
  action: string
  details?: string
  ip_address?: string
  resource_type?: string
  resource_id?: string
  timestamp: string
}

// Auth types
export interface AuthResponse {
  success: boolean
  access_token?: string
  error?: string
  user?: User
  must_change_credentials?: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  phone: string
  password: string
  full_name: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface UpdateProfileRequest {
  email?: string
  phone?: string
  full_name?: string
}

// Account types
export interface CreateAccountRequest {
  account_type: 'checking' | 'savings'
  opening_balance: number
}

export interface AccountResponse {
  success: boolean
  account?: Account
  error?: string
  message?: string
}

// Transaction types
export interface InternalTransferRequest {
  sender_account_id: number
  receiver_account_id: number
  amount: number
  description?: string
}

export interface ExternalTransferRequest {
  sender_account_id: number
  receiver_account_number: string
  amount: number
  description?: string
}

export interface TransactionResponse {
  success: boolean
  transaction?: Transaction
  error?: string
  message?: string
}

export interface TransactionHistory {
  transactions: Transaction[]
  total_count: number
}

// Dashboard types
export interface DashboardQuickLink {
  label: string
  path: string
}

export interface DashboardAccount extends Account {
  recent_transactions: Transaction[]
}

export interface DashboardResponse {
  accounts: DashboardAccount[]
  quick_links: DashboardQuickLink[]
}

// Support types
export interface CreateTicketRequest {
  subject: string
  description: string
  priority?: string
}

export interface UpdateTicketStatusRequest {
  status: 'open' | 'in_progress' | 'resolved'
}

export interface AddNoteRequest {
  note: string
  is_internal?: boolean
}

export interface TicketResponse {
  success: boolean
  ticket?: SupportTicket
  error?: string
  message?: string
}

export interface TicketListResponse {
  tickets: SupportTicket[]
  total_count: number
}

// Audit types
export interface AuditLogResponse {
  logs: AuditLog[]
  total_count: number
}
