import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { demoAPI } from '../services/api';
import PayPalConnectModal from '../components/settings/PayPalConnectModal';
import {
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Database,
  Layers,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  User,
  Home,
  Building2,
  Lock
} from 'lucide-react';

const OnboardingPage = () => {
  const { user, business, refreshBusiness, switchBusinessMode } = useAuth();
  const navigate = useNavigate();

  const [modalOpen, setModalOpen] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState(null);

  const accountType = business?.account_type || 'individual';
  const accountTypeName =
    accountType === 'individual'
      ? 'Personal Finances'
      : accountType === 'household'
      ? 'Household Budget'
      : 'Small Business';

  const markOnboarded = () => {
    if (user?.id) {
      localStorage.setItem(`subwise_onboarded_${user.id}`, 'true');
    }
  };

  const handleChooseDemo = async () => {
    try {
      setLoadingDemo(true);
      setError(null);
      // Initialize isolated demo dataset for this account type
      await demoAPI.generate();
      await switchBusinessMode('demo');
      await refreshBusiness();
      markOnboarded();
      navigate('/dashboard');
    } catch (err) {
      console.error('Demo onboarding initialization failed:', err);
      setError('Could not prepare demo environment. Please try again.');
      setLoadingDemo(false);
    }
  };

  const handleSkip = () => {
    markOnboarded();
    navigate('/dashboard');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-app)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2.5rem 1.5rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ width: '100%', maxWidth: '820px' }}>

        {/* Brand & Welcome Header */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #003087 0%, #0070ba 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 800,
            fontSize: '1.65rem',
            margin: '0 auto 1.25rem',
            boxShadow: '0 4px 14px rgba(0,48,135,0.2)',
          }}>P</div>

          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.35rem 0.85rem',
            borderRadius: '9999px',
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            color: '#0070ba',
            fontSize: '0.82rem',
            fontWeight: 700,
            marginBottom: '0.75rem'
          }}>
            {accountType === 'household' ? (
              <Home size={14} />
            ) : accountType === 'individual' ? (
              <User size={14} />
            ) : (
              <Building2 size={14} />
            )}
            <span>{accountTypeName} Account Created</span>
          </div>

          <h1 style={{
            fontSize: '2rem',
            fontWeight: 800,
            color: 'var(--navy-slate)',
            letterSpacing: '-0.025em',
            marginBottom: '0.5rem',
            lineHeight: 1.25,
          }}>
            Welcome to SubWise AI{user?.full_name ? `, ${user.full_name}` : ''}!
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.02rem', maxWidth: '580px', margin: '0 auto' }}>
            Choose how you would like to explore SubWise AI's automated subscription and cash-flow intelligence.
          </p>
        </div>

        {error && (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            borderRadius: '8px',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {/* 2-Option Onboarding Choice Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          {/* Option A: Explore Demo Mode */}
          <div
            className="fintech-card"
            style={{
              padding: '2rem 1.75rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              position: 'relative',
              border: '2px solid #3b82f6',
              boxShadow: '0 8px 24px rgba(59,130,246,0.08)'
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-12px',
              right: '20px',
              background: '#2563eb',
              color: '#ffffff',
              fontSize: '0.72rem',
              fontWeight: 800,
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Recommended
            </div>

            <div>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#eff6ff',
                color: '#2563eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem'
              }}>
                <Sparkles size={24} />
              </div>

              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                Explore with Sample Data
              </h2>
              <p style={{ fontSize: '0.9rem', color: '#64748b', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                Load realistic demonstration data tailored for {accountTypeName.toLowerCase()}. Instantly experience
                subscription detection, spending breakdowns, and AI savings directives without connecting external accounts.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <CheckCircle2 size={16} color="#059669" />
                  <span>Instant sandbox data with zero setup</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <CheckCircle2 size={16} color="#059669" />
                  <span>Completely isolated from real financial accounts</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <CheckCircle2 size={16} color="#059669" />
                  <span>Switch to real sandbox at any time</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleChooseDemo}
              disabled={loadingDemo}
              className="btn-fintech btn-fintech-primary"
              style={{
                width: '100%',
                padding: '0.85rem',
                fontSize: '0.95rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              <span>{loadingDemo ? 'Preparing Workspace...' : 'Launch Demo Workspace'}</span>
              <ArrowRight size={17} />
            </button>
          </div>

          {/* Option B: Connect PayPal Sandbox */}
          <div
            className="fintech-card"
            style={{
              padding: '2rem 1.75rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              border: '1px solid #e2e8f0'
            }}
          >
            <div>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#f8fafc',
                color: '#003087',
                border: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem'
              }}>
                <Layers size={24} />
              </div>

              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                Connect PayPal Sandbox
              </h2>
              <p style={{ fontSize: '0.9rem', color: '#64748b', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                Connect your PayPal Developer Sandbox API credentials to analyze real simulated test transactions.
                No real credit cards or financial payments are ever charged.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <ShieldCheck size={16} color="#0284c7" />
                  <span>PayPal Developer Sandbox &amp; OAuth 2.0</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <ShieldCheck size={16} color="#0284c7" />
                  <span>Optional for Individual &amp; Household users</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#334155' }}>
                  <ShieldCheck size={16} color="#0284c7" />
                  <span>Does not modify historical PayPal transactions</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setModalOpen(true)}
              className="btn-fintech btn-fintech-outline"
              style={{
                width: '100%',
                padding: '0.85rem',
                fontSize: '0.95rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              <span>Connect PayPal Credentials</span>
              <ChevronRight size={17} />
            </button>
          </div>
        </div>

        {/* Skip & Bottom Navigation */}
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={handleSkip}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748b',
              fontSize: '0.92rem',
              cursor: 'pointer',
              fontWeight: 600,
              textDecoration: 'underline'
            }}
          >
            Skip setup for now &amp; go directly to empty dashboard →
          </button>
        </div>

      </div>

      {/* Reusable PayPal Connect Modal */}
      <PayPalConnectModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConnected={() => {
          setModalOpen(false);
          markOnboarded();
          navigate('/dashboard');
        }}
      />
    </div>
  );
};

export default OnboardingPage;
