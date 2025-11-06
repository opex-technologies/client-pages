/**
 * Main Application Component
 * Sets up routing and provides authentication context
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Import pages (we'll create these next)
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TemplateListPage from './pages/TemplateListPage';
import TemplateEditorPage from './pages/TemplateEditorPage';
import QuestionDatabasePage from './pages/QuestionDatabasePage';
import DeploymentHistoryPage from './pages/DeploymentHistoryPage';
import ResponseListPage from './pages/ResponseListPage';
import ResponseDetailPage from './pages/ResponseDetailPage';

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
        }
      />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <DashboardPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/templates"
        element={
          <ProtectedRoute>
            <Layout>
              <TemplateListPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/templates/new"
        element={
          <ProtectedRoute requiredPermission="edit">
            <Layout>
              <TemplateEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/templates/:id/edit"
        element={
          <ProtectedRoute requiredPermission="edit">
            <Layout>
              <TemplateEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/questions"
        element={
          <ProtectedRoute>
            <Layout>
              <QuestionDatabasePage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/deployments"
        element={
          <ProtectedRoute>
            <Layout>
              <DeploymentHistoryPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/responses"
        element={
          <ProtectedRoute>
            <Layout>
              <ResponseListPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/responses/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <ResponseDetailPage />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Fallback - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#1a2859',
            },
            success: {
              iconTheme: {
                primary: '#00c4cc',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </Router>
  );
}

export default App;
