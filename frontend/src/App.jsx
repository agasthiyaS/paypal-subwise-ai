import React from 'react';
import { Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// Common layout components
import Navbar from './components/common/Navbar';
import Sidebar from './components/common/Sidebar';
import DemoDisclaimerBanner from './components/common/DemoDisclaimerBanner';

// Pages — public
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Pages — protected
import DashboardPage from './pages/DashboardPage';
import SubscriptionsPage from './pages/SubscriptionsPage';
import ForecastPage from './pages/ForecastPage';
import SimulatorPage from './pages/SimulatorPage';
import RecommendationsPage from './pages/RecommendationsPage';
import ReportsPage from './pages/ReportsPage';
import AssistantPage from './pages/AssistantPage';
import ExpensesPage from './pages/ExpensesPage';
import HouseholdPage from './pages/HouseholdPage';
import SavingsDiscoveryPage from './pages/SavingsDiscoveryPage';
import InsightsPage from './pages/InsightsPage';
import AdminPage from './pages/AdminPage';

/* ============================================================ */
/*  Loading Screen                                              */
/* ============================================================ */
const LoadingScreen = () => (
  <div style={{
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-app)',
    gap: '1rem'
  }}>
    <div style={{
      width: '48px',
      height: '48px',
      borderRadius: '12px',
      background: 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 800,
      fontSize: '1.5rem',
      boxShadow: '0 4px 14px rgba(0,48,135,0.25)'
    }}>P</div>
    <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem', fontWeight: 500 }}>
      Initializing PayPal SubWise AI...
    </div>
    <div style={{
      width: '160px',
      height: '3px',
      background: 'var(--border-light)',
      borderRadius: '99px',
      overflow: 'hidden'
    }}>
      <div style={{
        height: '100%',
        width: '50%',
        background: 'var(--paypal-blue)',
        borderRadius: '99px',
        animation: 'pulse 1.4s ease-in-out infinite'
      }} />
    </div>
  </div>
);

/* ============================================================ */
/*  Protected Layout — Sidebar + Navbar shell                  */
/* ============================================================ */
const ProtectedLayout = () => {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-viewport">
        <Navbar />
        <DemoDisclaimerBanner />
        <main className="content-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

/* ============================================================ */
/*  Public Layout — no sidebar, plain wrapper                  */
/* ============================================================ */
const PublicLayout = () => {
  const { token } = useAuth();
  // If already logged-in, bounce to dashboard
  if (token) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
};

/* ============================================================ */
/*  Root App                                                    */
/* ============================================================ */
function App() {
  const { loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return (
    <Routes>
      {/* Landing page — accessible regardless of auth */}
      <Route path="/" element={<LandingPage />} />

      {/* Public auth routes — redirect to dashboard if already logged in */}
      <Route element={<PublicLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected app routes */}
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/budgets" element={<ExpensesPage defaultTab="budget" />} />
        <Route path="/household" element={<HouseholdPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/savings-discovery" element={<SavingsDiscoveryPage />} />
        <Route path="/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/simulator" element={<SimulatorPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/transactions" element={<Navigate to="/dashboard" replace />} />
        <Route path="/settings" element={<Navigate to="/dashboard" replace />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
