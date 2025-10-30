import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

// Utils
import { isAuthenticated, getUserRole, getAuth } from './utils/auth';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import TowOperatorDashboard from './pages/TowOperatorDashboard';
import DealerDashboard from './pages/DealerDashboard';
import OwnerDashboard from './pages/OwnerDashboard';
import LeadDetails from './pages/LeadDetails';
import CreateLead from './pages/CreateLead';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const userRole = getUserRole();
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Dashboard Router based on role
const DashboardRouter = () => {
  const userRole = getUserRole();

  switch (userRole) {
    case 'tow_operator':
      return <TowOperatorDashboard />;
    case 'dealer':
      return <DealerDashboard />;
    case 'owner':
      return <OwnerDashboard />;
    default:
      return <Navigate to="/login" replace />;
  }
};

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const { user: authUser } = getAuth();
    setUser(authUser);
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            }
          />

          <Route
            path="/leads/create"
            element={
              <ProtectedRoute allowedRoles={['tow_operator']}>
                <CreateLead />
              </ProtectedRoute>
            }
          />

          <Route
            path="/leads/:id"
            element={
              <ProtectedRoute>
                <LeadDetails />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
