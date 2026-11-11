import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, LogOut, Layers, Lock, Settings, Sparkles, RefreshCw, Menu } from 'lucide-react';
import PayPalConnectModal from '../settings/PayPalConnectModal';
import { demoAPI } from '../../services/api';

const Navbar = ({ onToggleMobileNav }) => {
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

  const accountBadge = isDemo
    ? 'Demo Mode'
    : accountType === 'individual'
    ? 'Individual'
    : accountType === 'household'
    ? 'Household'
    : 'Business';

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  };

  const initials = getInitials(isDemo ? 'DemoTech' : business?.company_name || user?.email);

  return (
    <>
      <header className="top-navbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Mobile Menu Button */}
          {user && (
            <button
              onClick={onToggleMobileNav}
              className="mobile-nav-toggle"
              aria-label="Toggle navigation menu"
              style={{
                display: 'none',
                background: 'transparent',
                border: 'none',
                color: 'var(--navy-slate)',
                cursor: 'pointer',
                padding: '0.25rem',
              }}
            >
              <Menu size={20} />
            </button>
          )}

          <Link to={user ? '/dashboard' : '/'} className="nav-brand-group">
            <div className="nav-brand-logo">P</div>
            <div>
              <div className="nav-brand-title">
                PayPal <span>SubWise</span> AI
              </div>
            </div>
            <span className="nav-brand-badge">{accountBadge}</span>
          </Link>
        </div>

        <div className="nav-right-actions">
          {/* Environment Mode Switcher */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {isDemo ? (
                <>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      background: '#f5f3ff',
                      padding: '0.3rem 0.75rem',
                      borderRadius: '9999px',
                      border: '1px solid #ddd6fe',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: '#7c3aed',
                    }}
                    title="Active in isolated DemoTech Solutions profile"
                  >
                    <Sparkles size={14} color="#7c3aed" />
                    <span>Demo Data</span>
                  </div>
                  <button
                    onClick={() => handleToggleMode('sandbox')}
                    disabled={switching}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', minHeight: '32px' }}
                    title="Switch to Real PayPal Sandbox Environment"
                  >
                    {switching ? 'Switching...' : 'To Sandbox'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setModalOpen(true)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      background: isSandbox ? '#fef3c7' : isLive ? '#ecfdf5' : 'var(--bg-subtle)',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '9999px',
                      border: `1px solid ${isSandbox ? '#fde68a' : isLive ? '#a7f3d0' : 'var(--border-light)'}`,
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: isSandbox ? '#92400e' : isLive ? '#065f46' : 'var(--navy-primary)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                    title="Click to configure PayPal Developer Sandbox settings"
                  >
                    {isSandbox ? (
                      <>
                        <Layers size={14} color="#b45309" />
                        <span>Sandbox</span>
                      </>
                    ) : (
                      <>
                        <Lock size={14} color="#059669" />
                        <span>Live</span>
                      </>
                    )}
                    <Settings size={12} style={{ opacity: 0.6, marginLeft: '0.15rem' }} />
                  </button>
                  <button
                    onClick={() => handleToggleMode('demo')}
                    disabled={switching}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    style={{
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.8rem',
                      minHeight: '32px',
                      color: '#7c3aed',
                      borderColor: '#ddd6fe',
                      background: '#faf5ff',
                    }}
                    title="Switch to Demo Environment"
                  >
                    <Sparkles size={13} color="#7c3aed" />
                    <span>{switching ? '...' : 'Demo'}</span>
                  </button>
                </>
              )}
            </div>
          )}

          {/* User / Business Profile Avatar Pill */}
          {user ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                borderLeft: '1px solid var(--border-light)',
                paddingLeft: '0.85rem',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'var(--navy-primary)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  flexShrink: 0,
                }}
                title={user?.email}
              >
                {initials}
              </div>

              <div className="nav-user-meta" style={{ display: 'flex', flexDirection: 'column' }}>
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: 'var(--navy-slate)',
                    maxWidth: '130px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {isDemo ? 'DemoTech' : business?.company_name || 'My Account'}
                </span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    color: 'var(--text-muted)',
                    maxWidth: '130px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {user?.email}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="btn-fintech btn-fintech-outline btn-sm"
                title="Log Out of Workspace"
                style={{ padding: '0.35rem 0.55rem', minHeight: '32px', color: 'var(--text-muted)' }}
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Link to="/login" className="btn-fintech btn-fintech-outline btn-sm" style={{ minHeight: '32px' }}>
                Log In
              </Link>
              <Link to="/register" className="btn-fintech btn-fintech-primary btn-sm" style={{ minHeight: '32px' }}>
                Get Started
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Demo Banner */}
      {user && isDemo && (
        <div
          style={{
            background: 'linear-gradient(90deg, #6d28d9 0%, #4f46e5 100%)',
            color: '#ffffff',
            padding: '0.45rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.5rem',
            fontSize: '0.82rem',
            fontWeight: 500,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                background: '#ffffff',
                color: '#6d28d9',
                padding: '0.12rem 0.5rem',
                borderRadius: '9999px',
                fontWeight: 700,
                fontSize: '0.7rem',
                letterSpacing: '0.04em',
              }}
            >
              DEMO
            </span>
            <span>
              Isolated Profile: <strong>DemoTech Solutions</strong>. Real Sandbox records remain untouched.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                background: 'rgba(255, 255, 255, 0.16)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                color: '#ffffff',
                borderRadius: '5px',
                padding: '0.22rem 0.6rem',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 600,
              }}
              title="Safely regenerates standard illustrative dataset"
            >
              <RefreshCw size={12} className={resetting ? 'spin' : ''} />
              <span>{resetting ? 'Resetting...' : 'Reset Data'}</span>
            </button>
            <button
              onClick={() => handleToggleMode('sandbox')}
              disabled={switching}
              style={{
                background: '#ffffff',
                border: 'none',
                color: '#6d28d9',
                borderRadius: '5px',
                padding: '0.22rem 0.7rem',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
              }}
              title="Return to Sandbox"
            >
              Exit Demo
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
