import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Building2, User, Mail, Lock, Briefcase, ArrowRight, TrendingUp, DollarSign, ShieldCheck } from 'lucide-react';

const BUSINESS_CATEGORIES = [
  'Software & Technology Services',
  'E-Commerce & Retail',
  'Marketing & Creative Agency',
  'Professional Services (Law/Consulting)',
  'Healthcare & Wellness',
  'Education & Online Courses',
  'Finance & Accounting',
  'Manufacturing & Operations',
  'Real Estate',
  'Other',
];

/**
 * RegisterPage — business onboarding form.
 * Collects business details and financial baseline for cash-flow seeding.
 */
const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    company_name: '',
    owner_name: '',
    email: '',
    password: '',
    business_category: '',
    monthly_revenue: '',
    cash_reserves: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 2-step form

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleStep1Continue = (e) => {
    e.preventDefault();
    setError('');
    if (!form.company_name || !form.owner_name || !form.email || !form.password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (form.password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setStep(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!form.business_category) {
      setError('Please select a business category.');
      setLoading(false);
      return;
    }

    const payload = {
      company_name: form.company_name,
      full_name: form.owner_name,
      email: form.email.trim(),
      password: form.password,
      industry: form.business_category,
      monthly_baseline_revenue: parseFloat(form.monthly_revenue) || 0.0,
      current_cash_reserves: parseFloat(form.cash_reserves) || 0.0,
    };

    const res = await register(payload);
    if (res.success) {
      navigate('/dashboard');
    } else {
      setError(res.message);
      setLoading(false);
    }
  };

  const inputStyle = { width: '100%' };
  const iconStyle = { position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-caption)' };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-app)',
      padding: '2rem',
    }}>
      <div style={{ width: '100%', maxWidth: '580px' }}>
        {/* Header */}
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
            marginBottom: '0.45rem',
            lineHeight: 1.25,
          }}>
            Register Your Business
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.02rem' }}>
            Get cash-flow intelligence and subscription optimization in minutes
          </p>
        </div>

        {/* Step Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          marginBottom: '2rem',
        }}>
          {[1, 2].map((s) => (
            <React.Fragment key={s}>
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.78rem',
                fontWeight: 700,
                background: step >= s ? 'var(--navy-primary)' : 'var(--bg-subtle)',
                color: step >= s ? '#fff' : 'var(--text-muted)',
                border: `2px solid ${step >= s ? 'var(--navy-primary)' : 'var(--border-medium)'}`,
                transition: 'all 0.2s ease',
              }}>{s}</div>
              {s < 2 && (
                <div style={{
                  width: '48px',
                  height: '2px',
                  background: step > s ? 'var(--navy-primary)' : 'var(--border-light)',
                  borderRadius: '1px',
                  transition: 'all 0.2s ease',
                }} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Form Card */}
        <div className="fintech-card" style={{ padding: '2rem' }}>
          {/* Error */}
          {error && (
            <div style={{
              background: 'var(--rose-bg)',
              border: '1px solid var(--rose-border)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              fontSize: '0.85rem',
              color: 'var(--rose-dark)',
              marginBottom: '1.5rem',
            }}>
              ⚠ {error}
            </div>
          )}

          {/* STEP 1 — Account Details */}
          {step === 1 && (
            <form onSubmit={handleStep1Continue} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--text-muted)',
                marginBottom: '0.25rem',
              }}>Step 1 — Account Details</div>

              <div className="form-group">
                <label className="form-label">Business Name *</label>
                <div style={{ position: 'relative' }}>
                  <Building2 size={15} style={iconStyle} />
                  <input
                    className="form-input"
                    placeholder="Acme Cloud Dynamics LLC"
                    value={form.company_name}
                    onChange={(e) => handleChange('company_name', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Owner / CEO Name *</label>
                <div style={{ position: 'relative' }}>
                  <User size={15} style={iconStyle} />
                  <input
                    className="form-input"
                    placeholder="Sarah Jenkins"
                    value={form.owner_name}
                    onChange={(e) => handleChange('owner_name', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Business Email *</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={15} style={iconStyle} />
                  <input
                    type="email"
                    className="form-input"
                    placeholder="you@yourcompany.com"
                    value={form.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Password *</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={15} style={iconStyle} />
                  <input
                    type="password"
                    className="form-input"
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password *</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={15} style={iconStyle} />
                  <input
                    type="password"
                    className="form-input"
                    placeholder="••••••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <button
                type="submit"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  width: '100%',
                  padding: '0.85rem',
                  background: 'var(--navy-primary)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  marginTop: '0.5rem',
                  letterSpacing: '0.01em',
                }}
              >
                Continue to Financial Context
                <ArrowRight size={16} />
              </button>
            </form>
          )}

          {/* STEP 2 — Financial Context */}
          {step === 2 && (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--text-muted)',
                marginBottom: '0.25rem',
              }}>Step 2 — Financial Context</div>

              <div style={{
                background: 'var(--paypal-blue-subtle)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                padding: '0.85rem 1rem',
                fontSize: '0.82rem',
                color: 'var(--navy-primary)',
              }}>
                💡 This information seeds your cash-flow model. It is never shared with PayPal or third parties.
              </div>

              <div className="form-group">
                <label className="form-label">Business Category *</label>
                <div style={{ position: 'relative' }}>
                  <Briefcase size={15} style={iconStyle} />
                  <select
                    className="form-input"
                    value={form.business_category}
                    onChange={(e) => handleChange('business_category', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    required
                  >
                    <option value="">Select your industry…</option>
                    {BUSINESS_CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Estimated Monthly Revenue (USD)
                  <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <TrendingUp size={15} style={iconStyle} />
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g. 18500"
                    value={form.monthly_revenue}
                    onChange={(e) => handleChange('monthly_revenue', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    min="0"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Current Cash Reserves (USD)
                  <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <DollarSign size={15} style={iconStyle} />
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g. 52000"
                    value={form.cash_reserves}
                    onChange={(e) => handleChange('cash_reserves', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.4rem' }}
                    min="0"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(''); }}
                  style={{
                    flex: 1,
                    padding: '0.85rem',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    color: 'var(--text-body)',
                    cursor: 'pointer',
                  }}
                >
                  ← Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    flex: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '0.85rem',
                    background: 'var(--navy-primary)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.75 : 1,
                    letterSpacing: '0.01em',
                  }}
                >
                  {loading ? 'Creating Account…' : 'Launch Dashboard'}
                  <ArrowRight size={16} />
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer links */}
        <p style={{
          textAlign: 'center',
          marginTop: '1.5rem',
          fontSize: '0.875rem',
          color: 'var(--text-muted)',
        }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--paypal-blue)', fontWeight: 600, textDecoration: 'none' }}>
            Sign in
          </Link>
        </p>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
          marginTop: '1rem',
          color: 'var(--text-caption)',
          fontSize: '0.75rem',
        }}>
          <ShieldCheck size={13} />
          Bank-grade encryption · SOC 2 compliant infrastructure
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
