import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  User, AuthResponse, LoginRequest, RegisterRequest,
  ChangePasswordRequest, UpdateProfileRequest,
  Account, CreateAccountRequest, AccountResponse,
  Transaction, InternalTransferRequest, ExternalTransferRequest,
  TransactionResponse, TransactionHistory,
  SupportTicket, CreateTicketRequest, UpdateTicketStatusRequest,
  AddNoteRequest, TicketResponse, TicketListResponse,
  AuditLogResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

class ApiService {
  private api: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.accessToken = null;
          localStorage.removeItem('accessToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    // Load token from localStorage
    const token = localStorage.getItem('accessToken');
    if (token) {
      this.accessToken = token;
    }
  }

  setAccessToken(token: string): void {
    this.accessToken = token;
    localStorage.setItem('accessToken', token);
  }

  clearAccessToken(): void {
    this.accessToken = null;
    localStorage.removeItem('accessToken');
  }

  // ==================== Authentication ====================

  async register(data: RegisterRequest): Promise<AuthResponse> {
    try {
      const response = await this.api.post<AuthResponse>('/auth/register', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await this.api.post<AuthResponse>('/auth/login', data);
      if (response.data.access_token) {
        this.setAccessToken(response.data.access_token);
      }
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<{ success: boolean }> {
    try {
      const response = await this.api.post('/auth/logout');
      this.clearAccessToken();
      return response.data;
    } catch (error) {
      this.clearAccessToken();
      return { success: true };
    }
  }

  async getProfile(): Promise<User> {
    try {
      const response = await this.api.get<User>('/auth/profile');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async changePassword(data: ChangePasswordRequest): Promise<{ success: boolean }> {
    try {
      const response = await this.api.post('/auth/change-password', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    try {
      const response = await this.api.put<User>('/auth/profile', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Accounts ====================

  async createAccount(data: CreateAccountRequest): Promise<Account> {
    try {
      const response = await this.api.post<Account>('/accounts', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAccount(accountId: number): Promise<Account> {
    try {
      const response = await this.api.get<Account>(`/accounts/${accountId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getUserAccounts(userId: number): Promise<Account[]> {
    try {
      const response = await this.api.get<{ accounts: Account[] }>(`/accounts/user/${userId}`);
      return response.data.accounts;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAccountBalance(accountId: number): Promise<{ balance: number; status: string }> {
    try {
      const response = await this.api.get(`/accounts/${accountId}/balance`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async freezeAccount(accountId: number): Promise<AccountResponse> {
    try {
      const response = await this.api.post<AccountResponse>(`/accounts/${accountId}/freeze`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async unfreezeAccount(accountId: number): Promise<AccountResponse> {
    try {
      const response = await this.api.post<AccountResponse>(`/accounts/${accountId}/unfreeze`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async closeAccount(accountId: number): Promise<AccountResponse> {
    try {
      const response = await this.api.post<AccountResponse>(`/accounts/${accountId}/close`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Transactions ====================

  async internalTransfer(data: InternalTransferRequest): Promise<TransactionResponse> {
    try {
      const response = await this.api.post<TransactionResponse>('/transactions/internal-transfer', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async externalTransfer(data: ExternalTransferRequest): Promise<TransactionResponse> {
    try {
      const response = await this.api.post<TransactionResponse>('/transactions/external-transfer', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getTransaction(transactionId: string): Promise<Transaction> {
    try {
      const response = await this.api.get<Transaction>(`/transactions/${transactionId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAccountTransactions(accountId: number, limit = 10, offset = 0): Promise<TransactionHistory> {
    try {
      const response = await this.api.get<TransactionHistory>(
        `/transactions/account/${accountId}/history`,
        { params: { limit, offset } }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async filterTransactions(
    accountId: number,
    filters: {
      start_date?: string;
      end_date?: string;
      transaction_type?: string;
      min_amount?: number;
      max_amount?: number;
      limit?: number;
      offset?: number;
    }
  ): Promise<TransactionHistory> {
    try {
      const response = await this.api.get<TransactionHistory>(
        `/transactions/account/${accountId}/filter`,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Support Tickets ====================

  async createTicket(data: CreateTicketRequest): Promise<TicketResponse> {
    try {
      const response = await this.api.post<TicketResponse>('/support/tickets', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getTicket(ticketId: string): Promise<SupportTicket> {
    try {
      const response = await this.api.get<SupportTicket>(`/support/tickets/${ticketId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getOpenTickets(limit = 10, offset = 0): Promise<TicketListResponse> {
    try {
      const response = await this.api.get<TicketListResponse>('/support/tickets/open', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getCustomerTickets(customerId: number, limit = 10, offset = 0): Promise<TicketListResponse> {
    try {
      const response = await this.api.get<TicketListResponse>(
        `/support/tickets/customer/${customerId}`,
        { params: { limit, offset } }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async updateTicketStatus(ticketId: string, data: UpdateTicketStatusRequest): Promise<TicketResponse> {
    try {
      const response = await this.api.put<TicketResponse>(`/support/tickets/${ticketId}/status`, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async addNote(ticketId: string, data: AddNoteRequest): Promise<TicketResponse> {
    try {
      const response = await this.api.post<TicketResponse>(`/support/tickets/${ticketId}/notes`, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async assignTicket(ticketId: string, agentId: number): Promise<TicketResponse> {
    try {
      const response = await this.api.post<TicketResponse>(`/support/tickets/${ticketId}/assign`, {
        agent_id: agentId
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Audit Logs ====================

  async getAuditLogs(
    filters: {
      limit?: number;
      offset?: number;
      action?: string;
      user_id?: number;
      start_date?: string;
      end_date?: string;
    } = {}
  ): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>('/audit/logs', { params: filters });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getUserAuditLogs(userId: number, limit = 50, offset = 0): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>(`/audit/user/${userId}/logs`, {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getLoginAttempts(userId?: number, limit = 50, offset = 0): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>('/audit/login-attempts', {
        params: { user_id: userId, limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getSuspiciousActivities(limit = 50, offset = 0): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>('/audit/suspicious-activities', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAdminActions(limit = 50, offset = 0): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>('/audit/admin-actions', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAccountFreezeLogs(limit = 50, offset = 0): Promise<AuditLogResponse> {
    try {
      const response = await this.api.get<AuditLogResponse>('/audit/account-freeze-logs', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Admin ====================

  async getAllUsers(limit = 50, offset = 0): Promise<{ users: User[]; total_count: number }> {
    try {
      const response = await this.api.get('/admin/users', { params: { limit, offset } });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getUser(userId: number): Promise<User> {
    try {
      const response = await this.api.get<User>(`/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async assignRole(userId: number, role: string): Promise<{ success: boolean }> {
    try {
      const response = await this.api.put(`/admin/users/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getUsersByRole(role: string, limit = 50, offset = 0): Promise<{ users: User[]; total_count: number }> {
    try {
      const response = await this.api.get(`/admin/users/role/${role}`, { params: { limit, offset } });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async deactivateUser(userId: number): Promise<{ success: boolean }> {
    try {
      const response = await this.api.post(`/admin/users/${userId}/deactivate`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async activateUser(userId: number): Promise<{ success: boolean }> {
    try {
      const response = await this.api.post(`/admin/users/${userId}/activate`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async createAccountForUser(userId: number, accountType: 'checking' | 'savings', openingBalance: number = 0): Promise<any> {
    try {
      const response = await this.api.post(`/admin/users/${userId}/accounts`, {
        account_type: accountType,
        opening_balance: openingBalance
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAdminUserAccounts(userId: number): Promise<{ accounts: any[] }> {
    try {
      const response = await this.api.get(`/admin/users/${userId}/accounts`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ==================== Error Handling ====================

  private handleError(error: any): never {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.error || error.message;
      throw new Error(message);
    }
    throw error;
  }
}

export default new ApiService();
