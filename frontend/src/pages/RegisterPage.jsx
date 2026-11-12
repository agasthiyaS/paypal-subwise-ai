import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Building2,
  User,
  Home,
  Mail,
  Lock,
  Briefcase,
  ArrowRight,
  TrendingUp,
  DollarSign,
  ShieldCheck,
  CheckCircle2,
  Users,
  ShoppingCart,
  Zap,
  Sparkles,
  ChevronLeft
} from 'lucide-react';

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

const INDIVIDUAL_CONCERNS = [
  'Unused Subscriptions & App Charges',
  'Dining Out & Food Delivery Surcharges',
  'Impulse Online Shopping Leaks',
  'Banking & Hidden Service Fees',
  'Optimizing General Monthly Savings',
];

const HOUSEHOLD_PRIORITIES = [
  'Supermarket & Grocery Price Creep',
  'High Electricity, Gas & Water Bills',
  'Overlapping Family Streaming & Cloud Accounts',
  'Shared Internet & Telecom Bundles',
  'Roommate / Family Member Expense Attribution',
];

const RegisterPage = () => {
  const { register, isDemoUser, exitDemoSession } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Read preselected account type from URL (e.g. /register?type=household)
  const searchParams = new URLSearchParams(location.search);
  const typeParam = searchParams.get('type');
  const validTypes = ['individual', 'household', 'business'];
  const hasValidTypeParam = Boolean(typeParam && validTypes.includes(typeParam.toLowerCase()));
  const initialType = hasValidTypeParam ? typeParam.toLowerCase() : 'individual';

  // Selected account type: 'individual' | 'household' | 'business'
  const [accountType, setAccountType] = useState(initialType);

  const [form, setForm] = useState({
    // Common
    full_name: '',
    email: '',
    password: '',
    // Business specific
    company_name: '',
    business_category: 'Software & Technology Services',
    monthly_revenue: '',
    cash_reserves: '',
    // Individual specific
    monthly_income: '',
    savings_goal: '',
    individual_concern: INDIVIDUAL_CONCERNS[0],
    // Household specific
    household_name: '',
    household_members: '3',
    household_budget: '',
    household_priority: HOUSEHOLD_PRIORITIES[0],
  });

  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  // If account type was pre-selected from landing page, step 2 is active with ability to go back
  const [step, setStep] = useState(hasValidTypeParam ? 2 : 1);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleStep1Continue = (e) => {
    e.preventDefault();
    setStep(2);
  };

  const handleStep2Continue = (e) => {
    e.preventDefault();
    setError('');

    if (!form.full_name || !form.email || !form.password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (accountType === 'business' && !form.company_name.trim()) {
      setError('Please provide your business name.');
      return;
    }
    if (accountType === 'household' && !form.household_name.trim()) {
      setError('Please provide your household or family name.');
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

    setStep(3);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Prepare company_name and metadata based on accountType
    let resolvedCompanyName = '';
    let resolvedIndustry = '';
    let resolvedBaseline = 0.0;
    let resolvedReserves = 0.0;

    if (accountType === 'individual') {
      resolvedCompanyName = `${form.full_name.trim()}'s Finances`;
      resolvedIndustry = `Personal: ${form.individual_concern}`;
      resolvedBaseline = parseFloat(form.monthly_income) || 0.0;
      resolvedReserves = parseFloat(form.savings_goal) || 0.0;
    } else if (accountType === 'household') {
      resolvedCompanyName = form.household_name.trim();
      resolvedIndustry = `Household: ${form.household_priority} (${form.household_members} members)`;
      resolvedBaseline = parseFloat(form.household_budget) || 0.0;
      resolvedReserves = 0.0;
    } else {
      resolvedCompanyName = form.company_name.trim();
      resolvedIndustry = form.business_category || 'SaaS / Technology';
      resolvedBaseline = parseFloat(form.monthly_revenue) || 0.0;
      resolvedReserves = parseFloat(form.cash_reserves) || 0.0;
    }

    const payload = {
      account_type: accountType,
      company_name: resolvedCompanyName,
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
      industry: resolvedIndustry,
      monthly_baseline_revenue: resolvedBaseline,
      current_cash_reserves: resolvedReserves,
    };

    const res = await register(payload);
    if (res.success) {
      navigate('/onboarding');
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
      padding: '2.5rem 1.5rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ width: '100%', maxWidth: '640px' }}>

        {/* Demo Session Notice if currently in demo mode */}
        {isDemoUser && (
          <div style={{
            background: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            fontSize: '0.88rem',
            color: '#334155'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={16} color="#0070ba" />
              <span>You are exploring in Demo Mode. Registering will create your own dedicated account.</span>
            </div>
            <button
              onClick={() => exitDemoSession()}
              type="button"
              className="btn-fintech btn-fintech-outline"
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
            >
              Exit Demo
            </button>
          </div>
        )}

        {/* Top Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'inline-block' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #003087 0%, #0070ba 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 800,
              fontSize: '1.75rem',
              margin: '0 auto 1rem',
              boxShadow: '0 4px 16px rgba(0,48,135,0.2)',
            }}>P</div>
          </Link>
          <h1 style={{
            fontSize: '1.85rem',
            fontWeight: 800,
            color: 'var(--navy-slate)',
            letterSpacing: '-0.025em',
            marginBottom: '0.4rem',
            lineHeight: 1.25,
          }}>
            Create Your SubWise AI Account
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.98rem' }}>
            AI-powered financial intelligence &amp; savings tailored to how you spend
          </p>
        </div>

        {/* Step Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.75rem',
          marginBottom: '2rem',
        }}>
          {[
            { num: 1, label: 'Profile' },
            { num: 2, label: 'Security' },
            { num: 3, label: 'Baseline' }
          ].map((s, idx) => (
            <React.Fragment key={s.num}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  background: step >= s.num ? '#0070ba' : 'var(--bg-subtle)',
                  color: step >= s.num ? '#fff' : 'var(--text-muted)',
                  border: `2px solid ${step >= s.num ? '#0070ba' : 'var(--border-medium)'}`,
                  transition: 'all 0.2s ease',
                }}>{s.num}</div>
                <span style={{ fontSize: '0.82rem', fontWeight: step >= s.num ? 700 : 500, color: step >= s.num ? '#0070ba' : 'var(--text-muted)' }}>
                  {s.label}
                </span>
              </div>
              {idx < 2 && (
                <div style={{
                  width: '36px',
                  height: '2px',
                  background: step > s.num ? '#0070ba' : 'var(--border-light)',
                  borderRadius: '1px',
                  transition: 'all 0.2s ease',
                }} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Main Card */}
        <div className="fintech-card" style={{ padding: '2.25rem', backgroundColor: '#ffffff', borderRadius: '16px', border: '1.5px solid #e2e8f0', boxShadow: '0 8px 24px rgba(0,0,0,0.04)' }}>
          {/* Error Banner */}
          {error && (
            <div style={{
              background: 'var(--rose-bg)',
              border: '1px solid var(--rose-border)',
              borderRadius: 'var(--radius-md)',
              padding: '0.85rem 1rem',
              fontSize: '0.88rem',
              color: 'var(--rose-dark)',
              marginBottom: '1.5rem',
            }}>
              ⚠ {error}
            </div>
          )}

          {/* STEP 1: Select Account Type */}
          {step === 1 && (
            <div>
              <div style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#64748b',
                marginBottom: '1rem',
              }}>
                Step 1 of 3 — Choose Account Type
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                {/* Individual Option */}
                <div
                  onClick={() => setAccountType('individual')}
                  style={{
                    border: `2px solid ${accountType === 'individual' ? '#0070ba' : '#e2e8f0'}`,
                    backgroundColor: accountType === 'individual' ? '#eff6ff' : '#ffffff',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem'
                  }}
                >
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '10px',
                    backgroundColor: accountType === 'individual' ? '#0070ba' : '#f1f5f9',
                    color: accountType === 'individual' ? '#ffffff' : '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <User size={22} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Individual User</strong>
                      {accountType === 'individual' && <CheckCircle2 size={18} color="#0070ba" />}
                    </div>
                    <p style={{ margin: 0, fontSize: '0.88rem', color: '#475569', lineHeight: 1.45 }}>
                      Personal budgeters and professionals. Track personal income, detect zombie subscriptions, stop food delivery fee leaks, and get tailored savings advice.
                    </p>
                  </div>
                </div>

                {/* Household Option */}
                <div
                  onClick={() => setAccountType('household')}
                  style={{
                    border: `2px solid ${accountType === 'household' ? '#0070ba' : '#e2e8f0'}`,
                    backgroundColor: accountType === 'household' ? '#eff6ff' : '#ffffff',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem'
                  }}
                >
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '10px',
                    backgroundColor: accountType === 'household' ? '#0070ba' : '#f1f5f9',
                    color: accountType === 'household' ? '#ffffff' : '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <Home size={22} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Household &amp; Family</strong>
                      {accountType === 'household' && <CheckCircle2 size={18} color="#0070ba" />}
                    </div>
                    <p style={{ margin: 0, fontSize: '0.88rem', color: '#475569', lineHeight: 1.45 }}>
                      Couples, families, and roommates. Benchmark grocery store prices, catch electric and heating utility surges, and pool family streaming plans.
                    </p>
                  </div>
                </div>

                {/* Small Business Option */}
                <div
                  onClick={() => setAccountType('business')}
                  style={{
                    border: `2px solid ${accountType === 'business' ? '#0070ba' : '#e2e8f0'}`,
                    backgroundColor: accountType === 'business' ? '#eff6ff' : '#ffffff',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem'
                  }}
                >
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '10px',
                    backgroundColor: accountType === 'business' ? '#0070ba' : '#f1f5f9',
                    color: accountType === 'business' ? '#ffffff' : '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <Building2 size={22} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Small Business (SMB)</strong>
                      {accountType === 'business' && <CheckCircle2 size={18} color="#0070ba" />}
                    </div>
                    <p style={{ margin: 0, fontSize: '0.88rem', color: '#475569', lineHeight: 1.45 }}>
                      Startups, founders, and digital agencies. Sync PayPal transaction reporting, audit software subscription creep, and simulate runway cash flows.
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleStep1Continue}
                className="btn-fintech btn-fintech-primary"
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  fontSize: '0.95rem'
                }}
              >
                <span>Continue with {accountType === 'individual' ? 'Individual' : accountType === 'household' ? 'Household' : 'Business'}</span>
                <ArrowRight size={17} />
              </button>
            </div>
          )}

          {/* STEP 2: Profile & Security Details */}
          {step === 2 && (
            <form onSubmit={handleStep2Continue} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
              <div style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#64748b',
              }}>
                Step 2 of 3 — Profile &amp; Login Credentials
              </div>

              {/* Conditional Name Inputs */}
              {accountType === 'individual' && (
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <div style={{ position: 'relative' }}>
                    <User size={16} style={iconStyle} />
                    <input
                      className="form-input"
                      placeholder="e.g. Alex Morgan"
                      value={form.full_name}
                      onChange={(e) => handleChange('full_name', e.target.value)}
                      style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                      required
                    />
                  </div>
                </div>
              )}

              {accountType === 'household' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Household / Family Name *</label>
                    <div style={{ position: 'relative' }}>
                      <Home size={16} style={iconStyle} />
                      <input
                        className="form-input"
                        placeholder="e.g. The Morgan Household or Oak Street Apt 4B"
                        value={form.household_name}
                        onChange={(e) => handleChange('household_name', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        required
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Primary Contact Name *</label>
                    <div style={{ position: 'relative' }}>
                      <User size={16} style={iconStyle} />
                      <input
                        className="form-input"
                        placeholder="e.g. Alex Morgan"
                        value={form.full_name}
                        onChange={(e) => handleChange('full_name', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        required
                      />
                    </div>
                  </div>
                </>
              )}

              {accountType === 'business' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Company / Entity Name *</label>
                    <div style={{ position: 'relative' }}>
                      <Building2 size={16} style={iconStyle} />
                      <input
                        className="form-input"
                        placeholder="e.g. NovaTech SaaS Inc."
                        value={form.company_name}
                        onChange={(e) => handleChange('company_name', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        required
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Owner / Authorized Name *</label>
                    <div style={{ position: 'relative' }}>
                      <User size={16} style={iconStyle} />
                      <input
                        className="form-input"
                        placeholder="e.g. Sarah Jenkins"
                        value={form.full_name}
                        onChange={(e) => handleChange('full_name', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        required
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="form-group">
                <label className="form-label">Email Address *</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} style={iconStyle} />
                  <input
                    type="email"
                    className="form-input"
                    placeholder="you@domain.com"
                    value={form.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Password *</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={iconStyle} />
                  <input
                    type="password"
                    className="form-input"
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                    required
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password *</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={iconStyle} />
                  <input
                    type="password"
                    className="form-input"
                    placeholder="••••••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                    required
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(''); }}
                  style={{
                    padding: '0.85rem 1.25rem',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: '#64748b'
                  }}
                >
                  <ChevronLeft size={16} /> Back
                </button>

                <button
                  type="submit"
                  className="btn-fintech btn-fintech-primary"
                  style={{
                    flex: 1,
                    padding: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    fontSize: '0.95rem'
                  }}
                >
                  <span>Continue to Financial Baseline</span>
                  <ArrowRight size={17} />
                </button>
              </div>
            </form>
          )}

          {/* STEP 3: Financial Baseline & Context */}
          {step === 3 && (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#64748b',
              }}>
                Step 3 of 3 — Tailored Financial Baseline
              </div>

              <div style={{
                background: '#eff6ff',
                border: '1px solid #bfdbfe',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                fontSize: '0.85rem',
                color: '#003087',
                lineHeight: 1.5
              }}>
                💡 This seeds your initial savings suggestions and intelligence models. You can update or sync live PayPal records anytime.
              </div>

              {/* Individual Context */}
              {accountType === 'individual' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Primary Savings Focus</label>
                    <div style={{ position: 'relative' }}>
                      <Sparkles size={16} style={iconStyle} />
                      <select
                        className="form-input"
                        value={form.individual_concern}
                        onChange={(e) => handleChange('individual_concern', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                      >
                        {INDIVIDUAL_CONCERNS.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Estimated Monthly Net Income (USD)
                      <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <DollarSign size={16} style={iconStyle} />
                      <input
                        type="number"
                        className="form-input"
                        placeholder="e.g. 4200"
                        value={form.monthly_income}
                        onChange={(e) => handleChange('monthly_income', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        min="0"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Target Monthly Savings Goal (USD)
                      <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <TrendingUp size={16} style={iconStyle} />
                      <input
                        type="number"
                        className="form-input"
                        placeholder="e.g. 500"
                        value={form.savings_goal}
                        onChange={(e) => handleChange('savings_goal', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        min="0"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Household Context */}
              {accountType === 'household' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Primary Household Expense Priority</label>
                    <div style={{ position: 'relative' }}>
                      <Sparkles size={16} style={iconStyle} />
                      <select
                        className="form-input"
                        value={form.household_priority}
                        onChange={(e) => handleChange('household_priority', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                      >
                        {HOUSEHOLD_PRIORITIES.map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Household Size / Contributing Members</label>
                    <div style={{ position: 'relative' }}>
                      <Users size={16} style={iconStyle} />
                      <select
                        className="form-input"
                        value={form.household_members}
                        onChange={(e) => handleChange('household_members', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                      >
                        <option value="1">1 Person (Single Household)</option>
                        <option value="2">2 Persons (Couple / Roommates)</option>
                        <option value="3">3 Persons (Family / Small Household)</option>
                        <option value="4">4 Persons (Family)</option>
                        <option value="5+">5+ Persons (Large Household)</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Estimated Monthly Shared Budget (USD)
                      <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <DollarSign size={16} style={iconStyle} />
                      <input
                        type="number"
                        className="form-input"
                        placeholder="e.g. 3500"
                        value={form.household_budget}
                        onChange={(e) => handleChange('household_budget', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        min="0"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Business Context */}
              {accountType === 'business' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Industry / Business Category *</label>
                    <div style={{ position: 'relative' }}>
                      <Briefcase size={16} style={iconStyle} />
                      <select
                        className="form-input"
                        value={form.business_category}
                        onChange={(e) => handleChange('business_category', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        required
                      >
                        {BUSINESS_CATEGORIES.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Estimated Monthly Baseline Revenue (USD)
                      <span style={{ color: 'var(--text-caption)', fontWeight: 400, marginLeft: '0.5rem' }}>Optional</span>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <TrendingUp size={16} style={iconStyle} />
                      <input
                        type="number"
                        className="form-input"
                        placeholder="e.g. 18500"
                        value={form.monthly_revenue}
                        onChange={(e) => handleChange('monthly_revenue', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
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
                      <DollarSign size={16} style={iconStyle} />
                      <input
                        type="number"
                        className="form-input"
                        placeholder="e.g. 52000"
                        value={form.cash_reserves}
                        onChange={(e) => handleChange('cash_reserves', e.target.value)}
                        style={{ ...inputStyle, paddingLeft: '2.5rem' }}
                        min="0"
                      />
                    </div>
                  </div>
                </>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => { setStep(2); setError(''); }}
                  style={{
                    padding: '0.85rem 1.25rem',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: '#64748b'
                  }}
                >
                  <ChevronLeft size={16} /> Back
                </button>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-fintech btn-fintech-primary"
                  style={{
                    flex: 1,
                    padding: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    fontSize: '0.95rem'
                  }}
                >
                  {loading ? 'Creating Account…' : 'Complete Setup & Launch Dashboard'}
                  {!loading && <ArrowRight size={17} />}
                </button>
              </div>
            </form>
          )}

          {/* Login Link */}
          <div style={{
            marginTop: '1.75rem',
            textAlign: 'center',
            fontSize: '0.88rem',
            color: 'var(--text-muted)',
            borderTop: '1px solid var(--border-light)',
            paddingTop: '1.25rem',
          }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--navy-primary)', fontWeight: 700, textDecoration: 'none' }}>
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
