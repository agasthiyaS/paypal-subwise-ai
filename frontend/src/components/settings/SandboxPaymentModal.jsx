import React, { useState } from 'react';
import { paypalAPI } from '../../services/api';
import { X, CreditCard, ExternalLink, CheckCircle2, AlertTriangle, RefreshCw, ShieldCheck, ArrowRight } from 'lucide-react';

const SandboxPaymentModal = ({ isOpen, onClose, onSuccess }) => {
  const [step, setStep] = useState('ready'); // 'ready' | 'creating' | 'awaiting_approval' | 'capturing' | 'completed' | 'error'
  const [orderData, setOrderData] = useState(null);
  const [captureData, setCaptureData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleStartPayment = async () => {
    setStep('creating');
    setErrorMsg(null);

    try {
      const origin = typeof window !== 'undefined' && window.location?.origin
        ? window.location.origin
        : 'http://localhost:3000';

      // Create Order using PayPal Orders v2 API
      const res = await paypalAPI.createOrder({
        amount: 5.00,
        currency: 'USD',
        description: 'SubWise AI Sandbox Payment Test',
        return_url: `${origin}/dashboard?paypal_test=success`,
        cancel_url: `${origin}/dashboard?paypal_test=cancel`
      });

      setOrderData(res);
      setStep('awaiting_approval');

      // Open PayPal's official Sandbox approval window
      if (res.approve_url) {
        window.open(res.approve_url, '_blank', 'width=600,height=720,scrollbars=yes');
      }
    } catch (err) {
      console.error('Order creation error:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to initialize PayPal Sandbox Order.');
      setStep('error');
    }
  };

  const handleManualCapture = async () => {
    if (!orderData?.order_id) return;
    setStep('capturing');
    setErrorMsg(null);

    try {
      const res = await paypalAPI.captureOrder(orderData.order_id);
      setCaptureData(res);
      setStep('completed');
      if (onSuccess) onSuccess(res);
    } catch (err) {
      console.error('Capture error:', err);
      setErrorMsg(err.response?.data?.detail || 'Order capture failed. Ensure you completed and approved the payment in PayPal before capturing.');
      setStep('awaiting_approval');
    }
  };

  const handleReset = () => {
    setStep('ready');
    setOrderData(null);
    setCaptureData(null);
    setErrorMsg(null);
  };

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
          maxWidth: '580px',
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
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.65rem', color: 'var(--navy-slate)' }}>
              <CreditCard size={22} color="var(--amber-dark)" />
              PayPal Sandbox Payment Test
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.15rem 0.65rem',
                borderRadius: '9999px',
                background: '#fef3c7',
                color: '#b45309',
                border: '1px solid #fde68a'
              }}>
                SANDBOX ORDERS v2 API
              </span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Test Amount: $5.00 USD
              </span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem' }} aria-label="Close modal">
            <X size={22} />
          </button>
        </div>

        {/* Notice Card */}
        <div style={{
          background: '#fffbeb',
          border: '1px solid #fde68a',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          marginBottom: '1.25rem',
          fontSize: '0.92rem',
          color: '#92400e',
          lineHeight: 1.5
        }}>
          <strong>How this test works:</strong>
          <ol style={{ margin: '0.45rem 0 0 1.25rem', padding: 0 }}>
            <li>Generates a real order via PayPal's official <code>POST /v2/checkout/orders</code>.</li>
            <li>Opens the PayPal Sandbox checkout in a secure window.</li>
            <li>Log in with your <strong>Personal Sandbox buyer account</strong> and click <em>Pay Now</em>.</li>
            <li>SubWise AI securely captures the transaction and verifies <code>COMPLETED</code> status.</li>
          </ol>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div style={{
            background: '#fee2e2',
            border: '1px solid #fecaca',
            borderRadius: 'var(--radius-sm)',
            padding: '0.85rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
            color: 'var(--rose-dark)',
            fontSize: '0.92rem'
          }}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>{errorMsg}</div>
          </div>
        )}

        {/* Step: READY */}
        {step === 'ready' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--navy-slate)' }}>
                  SubWise AI Sandbox Payment Test
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                  Authentic PayPal Sandbox transaction verification
                </div>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--paypal-blue)' }}>
                $5.00 <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>USD</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button
                type="button"
                onClick={onClose}
                className="btn-fintech btn-fintech-outline"
                style={{ minHeight: '44px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleStartPayment}
                className="btn-fintech btn-fintech-primary"
                style={{ minHeight: '44px', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: '#0070ba' }}
              >
                <span>Launch PayPal Sandbox Checkout</span>
                <ExternalLink size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Step: CREATING ORDER */}
        {step === 'creating' && (
          <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
            <RefreshCw size={36} className="spin-icon" style={{ color: 'var(--paypal-blue)', margin: '0 auto 1rem' }} />
            <div style={{ fontWeight: 700, fontSize: '1.15rem', color: 'var(--navy-slate)' }}>
              Creating Sandbox Order...
            </div>
            <div style={{ fontSize: '0.92rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Communicating with PayPal Sandbox REST API (POST /v2/checkout/orders)
            </div>
          </div>
        )}

        {/* Step: AWAITING APPROVAL */}
        {step === 'awaiting_approval' && orderData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{
              background: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: 'var(--radius-md)',
              padding: '1.15rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#1e40af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                PayPal Order Created
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-primary)', marginTop: '0.25rem' }}>
                Order ID: {orderData.order_id}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-body)', marginTop: '0.5rem' }}>
                A PayPal Sandbox checkout window has been opened. Please sign in with your <strong>Personal Sandbox account</strong> and authorize the $5.00 payment.
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              {orderData.approve_url && (
                <a
                  href={orderData.approve_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-fintech btn-fintech-outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.92rem', textDecoration: 'none' }}
                >
                  <ExternalLink size={16} /> Reopen Checkout Window
                </a>
              )}
            </div>

            <div style={{
              background: '#f8fafc',
              border: '1px dashed var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              textAlign: 'center'
            }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
                Completed payment in PayPal?
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Click below to capture the payment on the backend and persist the transaction to the database.
              </p>
              <button
                type="button"
                onClick={handleManualCapture}
                className="btn-fintech btn-fintech-primary"
                style={{ minHeight: '44px', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'var(--emerald-dark)' }}
              >
                <CheckCircle2 size={18} />
                <span>Verify &amp; Capture Order</span>
              </button>
            </div>
          </div>
        )}

        {/* Step: CAPTURING */}
        {step === 'capturing' && (
          <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
            <RefreshCw size={36} className="spin-icon" style={{ color: 'var(--emerald-dark)', margin: '0 auto 1rem' }} />
            <div style={{ fontWeight: 700, fontSize: '1.15rem', color: 'var(--navy-slate)' }}>
              Capturing PayPal Order...
            </div>
            <div style={{ fontSize: '0.92rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Executing backend capture via Orders v2 API and verifying COMPLETED status
            </div>
          </div>
        )}

        {/* Step: COMPLETED */}
        {step === 'completed' && captureData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{
              background: '#dcfce7',
              border: '1px solid #86efac',
              borderRadius: 'var(--radius-md)',
              padding: '1.35rem',
              textAlign: 'center'
            }}>
              <CheckCircle2 size={40} style={{ color: 'var(--emerald-dark)', margin: '0 auto 0.5rem' }} />
              <div style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--emerald-dark)' }}>
                Payment Successfully Captured!
              </div>
              <div style={{ fontSize: '0.92rem', color: '#166534', marginTop: '0.25rem' }}>
                Verified COMPLETED on PayPal Sandbox Rails
              </div>
            </div>

            <div style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '1.15rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
              fontSize: '0.92rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Order ID:</span>
                <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{captureData.order_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>PayPal Capture TxID:</span>
                <span style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--paypal-blue)' }}>{captureData.capture_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Gross Amount:</span>
                <span style={{ fontWeight: 700 }}>${Number(captureData.gross_amount).toFixed(2)} {captureData.currency}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>PayPal Fee:</span>
                <span style={{ fontWeight: 700, color: 'var(--rose-dark)' }}>${Number(captureData.fee_amount || 0).toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Net Settled:</span>
                <span style={{ fontWeight: 700, color: 'var(--emerald-dark)' }}>${Number(captureData.net_amount).toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Database Status:</span>
                <span style={{ fontWeight: 700, color: 'var(--emerald-dark)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={16} /> Saved &amp; Deduplicated
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                onClose();
                handleReset();
              }}
              className="btn-fintech btn-fintech-primary"
              style={{ minHeight: '44px', width: '100%', justifyContent: 'center' }}
            >
              Done &amp; View in Dashboard
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default SandboxPaymentModal;

