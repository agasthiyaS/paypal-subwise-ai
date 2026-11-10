import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, ArrowRight, Lock, Mail, ShieldCheck, AlertCircle } from 'lucide-react';

/**
 * LoginPage — professional fintech sign-in with 1-click demo access
 * and authenticated workspace navigation.
 */
const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isDemoSubmitting, setIsDemoSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setLoading(true);
    try {
      const res = await login(cleanEmail, password);
      if (res.success) {
        navigate('/dashboard');
      } else {
        setError(res.message || 'Incorrect email or password. Please try again.');
      }
    } catch (err) {
      console.error('Login submit error:', err);
      setError('An unexpected error occurred while signing in. Please verify your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    setIsDemoSubmitting(true);
    setLoading(true);
    try {
      const res = await login('demo@subwise.io', 'DemoPass2026!');
      if (res.success) {
        navigate('/dashboard');
      } else {
        setError(res.message || 'Demo login failed. Please ensure the backend is running.');
      }
    } catch (err) {
      console.error('Demo login submit error:', err);
      setError('Unable to reach the backend service for demonstration login.');
    } finally {
      setLoading(false);
      setIsDemoSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: 'var(--bg-app)',
    }}>
      {/* Left decorative panel (visible on large displays) */}
      <div style={{
        display: 'none',
        flex: '1',
        background: 'var(--navy-slate)',
        padding: '3.5rem',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }} className="auth-side-panel">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.85rem',
        }}>
          <div className="nav-brand-logo">P</div>
          <div>
            <div className="nav-brand-title" style={{ color: '#fff', fontSize: '1.35rem' }}>
              PayPal <span style={{ color: '#38bdf8' }}>SubWise</span> AI
            </div>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>
              Subscription Intelligence Platform
            </div>
          </div>
        </div>

        <div>
          <div style={{ color: '#f1f5f9', fontSize: '1.85rem', fontWeight: 800, lineHeight: 1.35, marginBottom: '2rem', letterSpacing: '-0.02em' }}>
            "Eliminate hidden SaaS waste before it drains your operational runway."
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
            {[
              { label: 'Avg. monthly savings identified', value: '$548/mo' },
              { label: 'Subscription redundancy detection', value: '98% accuracy' },
              { label: 'Cash flow runway preserved', value: '+11 days avg.' },
            ].map((stat) => (
              <div key={stat.label} style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 'var(--radius-md)',
                padding: '1.1rem 1.35rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ color: '#cbd5e1', fontSize: '0.95rem', fontWeight: 500 }}>{stat.label}</span>
                <span style={{ color: '#38bdf8', fontWeight: 800, fontSize: '1.15rem', fontFamily: 'JetBrains Mono, monospace' }}>{stat.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ color: '#64748b', fontSize: '0.85rem' }}>
          © 2026 PayPal SubWise AI — Enterprise FinTech Solution
        </div>
      </div>

      {/* Right: Login form */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 2rem',
      }}>
        <div style={{ width: '100%', maxWidth: '520px' }}>
          {/* Brand header */}
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '18px',
              background: 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 800,
              fontSize: '1.85rem',
              margin: '0 auto 1.35rem',
              boxShadow: '0 4px 18px rgba(0,48,135,0.25)',
            }}>P</div>
            <h1 style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: 'var(--navy-slate)',
              letterSpacing: '-0.03em',
              marginBottom: '0.5rem',
              lineHeight: 1.25,
            }}>
              Welcome Back
            </h1>
            <p style={{ color: 'var(--text-body)', fontSize: '1.05rem' }}>
              Sign in to your SubWise AI workspace
            </p>
          </div>

          {/* Demo CTA */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.65rem',
              padding: '1.05rem 1.35rem',
              background: 'linear-gradient(135deg, #003087 0%, #0070ba 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: '1.05rem',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading && !isDemoSubmitting ? 0.75 : 1,
              marginBottom: '1.75rem',
              letterSpacing: '0.01em',
              boxShadow: '0 4px 16px rgba(0,48,135,0.25)',
              transition: 'all 0.15s ease',
              minHeight: '52px',
            }}
          >
            {isDemoSubmitting ? (
              <>
                <span className="spinner-border" />
                <span>Launching Demo Workspace…</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Explore Live Demo — 1 Click</span>
              </>
            )}
          </button>

          {/* Divider */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.85rem',
            marginBottom: '1.5rem',
          }}>
            <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }} />
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
              or sign in with email
            </span>
            <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }} />
          </div>

          {/* Error Banner */}
          {error && (
            <div style={{
              background: 'var(--rose-bg)',
              border: '1.5px solid var(--rose-border)',
              borderRadius: 'var(--radius-md)',
              padding: '0.9rem 1.15rem',
              fontSize: '0.95rem',
              color: 'var(--rose-dark)',
              marginBottom: '1.35rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              lineHeight: 1.45,
            }}>
              <AlertCircle size={20} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={17} style={{
                  position: 'absolute', left: '14px', top: '50%',
                  transform: 'translateY(-50%)', color: 'var(--text-caption)',
                }} />
                <input
                  id="login-email"
                  type="email"
                  className="form-input"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ paddingLeft: '2.6rem' }}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="login-password">
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={17} style={{
                  position: 'absolute', left: '14px', top: '50%',
                  transform: 'translateY(-50%)', color: 'var(--text-caption)',
                }} />
                <input
                  id="login-password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ paddingLeft: '2.6rem' }}
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              id="btn-sign-in"
              type="submit"
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.65rem',
                width: '100%',
                padding: '1.05rem 1.35rem',
                background: 'var(--navy-primary)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: '1.05rem',
                fontWeight: 700,
                color: '#ffffff',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.8 : 1,
                transition: 'all 0.15s ease',
                marginTop: '0.65rem',
                boxShadow: '0 4px 14px rgba(0,48,135,0.25)',
                minHeight: '52px',
              }}
            >
              {loading && !isDemoSubmitting ? (
                <>
                  <span className="spinner-border" />
                  <span>Authenticating to Workspace…</span>
                </>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>

          {/* Switch to register */}
          <p style={{
            textAlign: 'center',
            marginTop: '2.25rem',
            fontSize: '1.02rem',
            color: 'var(--text-body)',
          }}>
            New to SubWise AI?{' '}
            <Link to="/register" style={{
              color: 'var(--paypal-blue)',
              fontWeight: 700,
              textDecoration: 'none',
            }}>
              Register your business
            </Link>
          </p>

          {/* Security badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            marginTop: '1.5rem',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}>
            <ShieldCheck size={16} color="var(--emerald-dark)" />
            <span>Bank-grade 256-bit encryption &amp; OAuth 2.0 security</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
