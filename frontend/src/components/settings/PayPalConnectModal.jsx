import React, { useState, useEffect } from 'react';
import { businessAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { X, Shield, Layers, Database, AlertTriangle, CheckCircle2, Lock, Eye, EyeOff, Unlink } from 'lucide-react';

const PayPalConnectModal = ({ isOpen, onClose, onConnected }) => {
  const { business, refreshBusiness } = useAuth();

  const [mode, setMode] = useState('sandbox');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  useEffect(() => {
    if (business) {
      setMode(business.paypal_mode || 'sandbox');
      // Never prefill secret from client state for security
      setClientId('');
      setClientSecret('');
    }
    setStatusMsg(null);
  }, [business, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg(null);

    try {
      const res = await businessAPI.connectPayPal({
        paypal_mode: mode,
        paypal_client_id: mode === 'demo' ? null : clientId,
        paypal_client_secret: mode === 'demo' ? null : clientSecret,
      });

      setStatusMsg({ type: 'success', text: res.message });
      await refreshBusiness();
      if (onConnected) onConnected();
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Connection verification failed. Please check credentials and try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Disconnect PayPal integration and switch to demonstration mode?')) {
      return;
    }
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await businessAPI.disconnectPayPal();
      setStatusMsg({ type: 'success', text: res.message });
      await refreshBusiness();
      if (onConnected) onConnected();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Disconnect failed.',
      });
    } finally {
      setLoading(false);
    }
  };

  const isCurrentlySandboxOrLive = business?.paypal_connected && business?.paypal_mode !== 'demo';

  return (
    <div
      className="modal-overlay fintech-modal-overlay"
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(15, 23, 42, 0.72)',
        backdropFilter: 'blur(5px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1.5rem',
        overflowY: 'auto'
      }}
    >
      <div
        className="modal-content fintech-modal-body"
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-xl)',
          maxWidth: '540px',
          width: '92%',
          padding: '2.25rem',
          boxShadow: 'var(--shadow-modal), 0 25px 50px -12px rgba(0, 0, 0, 0.35)',
          border: '1px solid var(--border-light)',
          maxHeight: '90vh',
          overflowY: 'auto',
          position: 'relative',
          zIndex: 10000,
          margin: 'auto'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--navy-slate)' }}>
            <span style={{ color: 'var(--paypal-blue)' }}>PayPal</span> Developer Sandbox & Live Setup
          </h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        {/* Security Notice */}
        <div style={{
          background: 'var(--paypal-blue-subtle)',
          border: '1px solid #bae6fd',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem',
          marginBottom: '1.25rem',
          fontSize: '0.82rem',
          color: 'var(--navy-primary)',
          lineHeight: '1.45'
        }}>
          <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.2rem' }}>
            <Shield size={15} color="var(--paypal-blue)" /> Sandbox Security Guarantee
          </div>
          SubWise AI accesses the official PayPal REST Reporting API via OAuth 2.0. Client Secrets are never sent to the browser or stored in client state.
        </div>

        <form onSubmit={handleSubmit}>
          {/* Mode Selector */}
          <div className="form-group">
            <label className="form-label" style={{ fontWeight: 600 }}>Integration Environment</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginTop: '0.35rem' }}>
              <div
                onClick={() => setMode('sandbox')}
                style={{
                  border: `2px solid ${mode === 'sandbox' ? 'var(--paypal-blue)' : 'var(--border-light)'}`,
                  background: mode === 'sandbox' ? 'var(--paypal-blue-subtle)' : 'var(--card-bg)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 0.5rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Layers size={22} style={{ margin: '0 auto 0.4rem', color: 'var(--amber-dark)' }} />
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-slate)' }}>Sandbox</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PayPal dev API</div>
              </div>

              <div
                onClick={() => setMode('demo')}
                style={{
                  border: `2px solid ${mode === 'demo' ? 'var(--paypal-blue)' : 'var(--border-light)'}`,
                  background: mode === 'demo' ? 'var(--paypal-blue-subtle)' : 'var(--card-bg)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 0.5rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Database size={22} style={{ margin: '0 auto 0.4rem', color: 'var(--navy-primary)' }} />
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-slate)' }}>Demo Mode</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Verified sample</div>
              </div>

              <div
                onClick={() => setMode('live')}
                style={{
                  border: `2px solid ${mode === 'live' ? 'var(--paypal-blue)' : 'var(--border-light)'}`,
                  background: mode === 'live' ? 'var(--paypal-blue-subtle)' : 'var(--card-bg)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 0.5rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Lock size={22} style={{ margin: '0 auto 0.4rem', color: 'var(--emerald-dark)' }} />
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-slate)' }}>Live API</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Production rails</div>
              </div>
            </div>
          </div>

          {/* Credentials only needed for sandbox / live */}
          {mode !== 'demo' && (
            <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Enter your REST App credentials from <a href="https://developer.paypal.com/dashboard/applications" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--paypal-blue)', fontWeight: 600 }}>developer.paypal.com</a>. Ensure the <strong>Transaction Search</strong> feature is enabled on your app.
              </div>

              <div className="form-group" style={{ marginBottom: '0.85rem' }}>
                <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>PayPal REST Client ID</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. A21AAJ... or your sandbox client ID"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  required={mode !== 'demo'}
                  style={{ fontSize: '0.85rem' }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '0' }}>
                <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>PayPal REST Client Secret</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showSecret ? 'text' : 'password'}
                    className="form-control"
                    placeholder="e.g. EMLk89... or your sandbox secret"
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    required={mode !== 'demo'}
                    style={{ fontSize: '0.85rem', paddingRight: '2.5rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    style={{
                      position: 'absolute',
                      right: '0.6rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer'
                    }}
                    title={showSecret ? 'Hide secret' : 'Show secret'}
                  >
                    {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {statusMsg && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              marginBottom: '1rem',
              background: statusMsg.type === 'success' ? '#dcfce7' : '#fee2e2',
              color: statusMsg.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
              border: `1px solid ${statusMsg.type === 'success' ? '#bbf7d0' : '#fecaca'}`
            }}>
              {statusMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <span>{statusMsg.text}</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
            <div>
              {isCurrentlySandboxOrLive && (
                <button
                  type="button"
                  onClick={handleDisconnect}
                  disabled={loading}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ color: 'var(--rose-dark)', borderColor: '#fca5a5' }}
                  title="Disconnect and return to demonstration dataset"
                >
                  <Unlink size={14} style={{ marginRight: '0.3rem' }} /> Disconnect
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="button" onClick={onClose} className="btn-fintech btn-fintech-outline btn-sm">
                Cancel
              </button>
              <button type="submit" disabled={loading} className="btn-fintech btn-fintech-primary btn-sm">
                {loading ? 'Verifying with PayPal...' : 'Save & Link Environment'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PayPalConnectModal;
