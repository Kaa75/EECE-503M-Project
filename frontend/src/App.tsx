import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage.tsx'
import RegisterPage from './pages/RegisterPage.tsx'
import DashboardPage from './pages/DashboardPage.tsx'
import ChangeCredentialsPage from './pages/ChangeCredentialsPage.tsx'
import AccountsPage from './pages/AccountsPage.tsx'
import TransactionsPage from './pages/TransactionsPage.tsx'
import SupportPage from './pages/SupportPage.tsx'
import AdminPage from './pages/AdminPage.tsx'
import AuditPage from './pages/AuditPage.tsx'
import ProfilePage from './pages/ProfilePage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import ProtectedRoute from './components/ProtectedRoute.tsx'
import { UserRole } from './types'
import LoadingSpinner from './components/LoadingSpinner.tsx'
import InternalTransferPage from './pages/InternalTransferPage.tsx'
import ExternalTransferPage from './pages/ExternalTransferPage.tsx'
import BillsPage from './pages/BillsPage.tsx'

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/change-credentials"
          element={
            <ProtectedRoute>
              <ChangeCredentialsPage />
            </ProtectedRoute>
          }
        />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/accounts"
          element={
            <ProtectedRoute>
              <AccountsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/transactions"
          element={
            <ProtectedRoute>
              <TransactionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/transfer/internal"
          element={
            <ProtectedRoute>
              <InternalTransferPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/transfer/external"
          element={
            <ProtectedRoute>
              <ExternalTransferPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/support"
          element={
            <ProtectedRoute requiredRoles={[UserRole.CUSTOMER, UserRole.SUPPORT_AGENT, UserRole.ADMIN]}>
              <SupportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/bills"
          element={
            <ProtectedRoute>
              <BillsPage />
            </ProtectedRoute>
          }
        />

        {/* Admin routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRoles={[UserRole.ADMIN]}>
              <AdminPage />
            </ProtectedRoute>
          }
        />

        {/* Audit routes */}
        <Route
          path="/audit"
          element={
            <ProtectedRoute requiredRoles={[UserRole.AUDITOR, UserRole.ADMIN]}>
              <AuditPage />
            </ProtectedRoute>
          }
        />

        {/* Default route */}
        <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />

        {/* 404 route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  )
}

export default App
