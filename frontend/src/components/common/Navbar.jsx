import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, LogOut, Database, Layers, Lock, Settings, Sparkles, RefreshCw } from 'lucide-react';
import PayPalConnectModal from '../settings/PayPalConnectModal';
import { demoAPI } from '../../services/api';

const Navbar = () => {
  const { user, business, logout, isDemoMode, switchBusinessMode, refreshBusiness } = useAuth();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [resetting, setResetting] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleToggleMode = async (targetMode) => {
    try {
      setSwitching(true);
      if (targetMode === 'demo') {
        // Generate or ensure demo data exists
        await demoAPI.generate();
      }
      await switchBusinessMode(targetMode);
      await refreshBusiness();
      window.location.reload();
    } catch (err) {
      console.error('Mode toggle failed:', err);
    } finally {
      setSwitching(false);
    }
  };

  const handleResetDemo = async () => {
    try {
      setResetting(true);
      await demoAPI.reset();
      await refreshBusiness();
      window.location.reload();
    } catch (err) {
      console.error('Demo reset failed:', err);
    } finally {
      setResetting(false);
    }
  };

  const isDemo = Boolean(business?.is_demo || isDemoMode);
  const paypalMode = business?.paypal_mode || 'sandbox';
  const isSandbox = !isDemo && paypalMode === 'sandbox';
  const isLive = !isDemo && paypalMode === 'live';

  const accountType = business?.account_type || 'business';
  const accountTagline = accountType === 'individual'
    ? 'Personal Financial Intelligence & Savings'
    : accountType === 'household'
    ? 'Household Budget & Shared Savings Intelligence'
    : 'Fintech Cash-Flow & Subscription Intelligence';

  const accountBadge = isDemo
    ? 'Demo Mode'
    : accountType === 'individual'
    ? 'Individual Edition'
    : accountType === 'household'
    ? 'Household Edition'
    : 'Business Edition';

  return (
    <>
      <header className="top-navbar">
        <Link to="/" className="nav-brand-group">
          <div className="nav-brand-logo">P</div>
          <div>
            <div className="nav-brand-title">
              PayPal <span>SubWise</span> AI
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.02em' }}>
              {accountTagline}
            </div>
          </div>
          <span className="nav-brand-badge">{accountBadge}</span>
        </Link>

        <div className="nav-right-actions">
          {/* Environment Mode Switcher / Indicator */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              {isDemo ? (
                <>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.55rem',
                      background: '#ede9fe',
                      padding: '0.45rem 1rem',
                      borderRadius: '9999px',
                      border: '1.5px solid #c4b5fd',
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      color: '#6d28d9',
                    }}
                    title="Active in isolated DemoTech Solutions profile"
                  >
                    <Sparkles size={16} color="#7c3aed" />
                    <span>Demo Mode (DemoTech)</span>
                  </div>
                  <button
                    onClick={() => handleToggleMode('sandbox')}
                    disabled={switching}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem', minHeight: '36px' }}
                    title="Switch to Real PayPal Sandbox Environment"
                  >
                    {switching ? 'Switching...' : 'Switch to Sandbox'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setModalOpen(true)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.55rem',
                      background: isSandbox ? '#fef3c7' : isLive ? '#dcfce7' : 'var(--bg-subtle)',
                      padding: '0.45rem 1rem',
                      borderRadius: '9999px',
                      border: `1.5px solid ${isSandbox ? '#fde68a' : isLive ? '#bbf7d0' : 'var(--border-light)'}`,
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      color: isSandbox ? 'var(--amber-dark)' : isLive ? 'var(--emerald-dark)' : 'var(--navy-primary)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    title="Click to configure PayPal Developer Sandbox settings"
                  >
                    {isSandbox ? (
                      <>
                        <Layers size={17} color="var(--amber-dark)" />
                        <span>PayPal Sandbox</span>
                      </>
                    ) : (
                      <>
                        <Lock size={17} color="var(--emerald-dark)" />
                        <span>PayPal Live</span>
                      </>
                    )}
                    <Settings size={14} style={{ opacity: 0.65, marginLeft: '0.3rem' }} />
                  </button>
                  <button
                    onClick={() => handleToggleMode('demo')}
                    disabled={switching}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.4rem 0.85rem',
                      background: '#ede9fe',
                      color: '#6d28d9',
                      border: '1.5px solid #c4b5fd',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      minHeight: '36px'
                    }}
                    title="Switch to Demo Environment with rich illustrative 6-month historical data"
                  >
                    <Sparkles size={15} color="#7c3aed" />
                    <span>{switching ? 'Loading Demo...' : 'Demo Mode'}</span>
                  </button>
                </>
              )}
            </div>
          )}

          {/* User / Business Profile Header */}
          {user ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1.15rem',
              borderLeft: '1.5px solid var(--border-light)',
              paddingLeft: '1.25rem'
            }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
                  {isDemo ? 'DemoTech Solutions' : (business?.company_name || 'My Business')}
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                  {user?.email || 'Authenticated User'}
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="btn-fintech btn-fintech-outline btn-sm"
                title="Log Out of Workspace"
                style={{ padding: '0.55rem 0.75rem', minHeight: '40px' }}
              >
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Link to="/login" className="btn-fintech btn-fintech-outline btn-sm">
                Log In
              </Link>
              <Link to="/register" className="btn-fintech btn-fintech-primary btn-sm">
                Get Started
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Prominent Global Banner when in Demo Mode */}
      {user && isDemo && (
        <div style={{
          background: 'linear-gradient(90deg, #6d28d9 0%, #4f46e5 100%)',
          color: '#ffffff',
          padding: '0.55rem 1.75rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          fontSize: '0.88rem',
          fontWeight: 600,
          borderBottom: '2px solid #5b21b6',
          boxShadow: '0 2px 8px rgba(109, 40, 217, 0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{
              background: '#ffffff',
              color: '#6d28d9',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontWeight: 800,
              fontSize: '0.75rem',
              letterSpacing: '0.04em'
            }}>DEMO MODE</span>
            <span>
              Isolated Business Profile: <strong>DemoTech Solutions</strong> (Software Services). Illustrative 6-month historical dataset loaded. Real Sandbox records remain untouched.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                background: 'rgba(255, 255, 255, 0.18)',
                border: '1px solid rgba(255, 255, 255, 0.35)',
                color: '#ffffff',
                borderRadius: '6px',
                padding: '0.3rem 0.75rem',
                cursor: 'pointer',
                fontSize: '0.82rem',
                fontWeight: 700
              }}
              title="Safely regenerates the standard 6-month illustrative dataset"
            >
              <RefreshCw size={13} className={resetting ? 'spin' : ''} />
              <span>{resetting ? 'Resetting...' : 'Reset Demo Data'}</span>
            </button>
            <button
              onClick={() => handleToggleMode('sandbox')}
              disabled={switching}
              style={{
                background: '#ffffff',
                border: 'none',
                color: '#6d28d9',
                borderRadius: '6px',
                padding: '0.3rem 0.85rem',
                cursor: 'pointer',
                fontSize: '0.82rem',
                fontWeight: 800
              }}
              title="Return to real Sandbox environment"
            >
              Exit to Sandbox
            </button>
          </div>
        </div>
      )}

      <PayPalConnectModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConnected={() => setModalOpen(false)}
      />
    </>
  );
};

export default Navbar;
