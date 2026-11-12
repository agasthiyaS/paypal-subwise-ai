import React from 'react';
import { Routes, Route, Navigate, Outlet, useLocation, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { ShieldCheck } from 'lucide-react';

// Common layout components
import Navbar from './components/common/Navbar';
import Sidebar from './components/common/Sidebar';
import DemoDisclaimerBanner from './components/common/DemoDisclaimerBanner';

// Pages — public & onboarding
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import OnboardingPage from './pages/OnboardingPage';

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
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const location = useLocation();

  React.useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  if (!token) return <Navigate to="/login" replace />;
  return (
    <div className="app-layout">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      {mobileOpen && <div className="mobile-nav-backdrop" onClick={() => setMobileOpen(false)} />}
      <div className="main-viewport">
        <Navbar onToggleMobileNav={() => setMobileOpen((prev) => !prev)} />
        <DemoDisclaimerBanner />
        <main className="content-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

/* ============================================================ */
/*  Public Layout — with session intent & account switcher     */
/* ============================================================ */
const PublicLayout = () => {
  const { token, user, business, isDemoUser, logout } = useAuth();

  // If no session token, render the public auth forms immediately
  if (!token) return <Outlet />;

  // If currently in a Demo Mode session (e.g. demo@subwise.io):
  // Allow accessing /register and /login without redirect loop
  if (isDemoUser) {
    return <Outlet />;
  }

  // If a genuine authenticated user attempts to visit /login or /register:
  // Render an explicit Account Switcher screen so we never silently clear sessions or trap the user
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-app)',
      padding: '2rem 1.5rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div className="fintech-card" style={{ maxWidth: '460px', width: '100%', padding: '2.5rem 2rem', textAlign: 'center' }}>
        <div style={{
          width: '52px',
          height: '52px',
          borderRadius: '16px',
          background: '#eff6ff',
          color: '#0070ba',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.25rem'
        }}>
          <ShieldCheck size={28} />
        </div>
        <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
          Already Signed In
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
          You are currently signed in as <strong>{user?.email || 'Active User'}</strong>
          {business?.company_name ? ` (${business.company_name})` : ''}.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Link
            to="/dashboard"
            className="btn-fintech btn-fintech-primary"
            style={{ width: '100%', padding: '0.75rem', justifyContent: 'center', textDecoration: 'none' }}
          >
            Continue to Dashboard
          </Link>
          <button
            onClick={() => logout()}
            className="btn-fintech btn-fintech-outline"
            style={{ width: '100%', padding: '0.75rem', justifyContent: 'center' }}
          >
            Sign Out to Switch Accounts
          </button>
        </div>
      </div>
    </div>
  );
};

/* ============================================================ */
/*  Root App                                                    */
/* ============================================================ */
function App() {
  const { loading, token } = useAuth();

  if (loading) return <LoadingScreen />;

  return (
    <Routes>
      {/* Landing page — accessible regardless of auth */}
      <Route path="/" element={<LandingPage />} />

      {/* Public auth routes — allow demo users to register, prompt genuine users */}
      <Route element={<PublicLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Post-Registration Onboarding (standalone layout for newly created accounts) */}
      <Route path="/onboarding" element={token ? <OnboardingPage /> : <Navigate to="/login" replace />} />

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
