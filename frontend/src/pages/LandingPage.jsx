import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  TrendingUp,
  Sliders,
  Sparkles,
  ArrowRight,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Database,
  BarChart3,
  User,
  Home,
  Building2,
  DollarSign,
  ShoppingCart,
  Zap,
  CreditCard,
  Percent,
  Search,
  Lock,
  ChevronRight
} from 'lucide-react';

const LandingPage = () => {
  const [activeAudience, setActiveAudience] = useState('individual'); // 'individual' | 'household' | 'business'

  // Interactive Savings Calculator State
  const [subSpend, setSubSpend] = useState(120);
  const [grocerySpend, setGrocerySpend] = useState(650);
  const [utilitySpend, setUtilitySpend] = useState(280);

  // Computed potential annual savings
  const estimatedAnnualSavings = Math.round((subSpend * 0.22 + grocerySpend * 0.14 + utilitySpend * 0.10) * 12);
  const threeYearAccumulated = Math.round(estimatedAnnualSavings * 3.15); // with mild compounding

  return (
    <div style={{ backgroundColor: '#ffffff', minHeight: '100vh', display: 'flex', flexDirection: 'column', color: '#1e293b', fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      
      {/* Top Value Banner */}
      <div style={{
        backgroundColor: '#002c6c',
        color: '#ffffff',
        padding: '0.75rem 1.5rem',
        textAlign: 'center',
        fontSize: '0.9rem',
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem'
      }}>
        <span style={{ background: '#0070ba', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>New Evolution</span>
        <span>PayPal SubWise AI: Your AI-Powered Financial Intelligence and Savings Assistant</span>
      </div>

      {/* Main Navigation Bar */}
      <header style={{
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 2.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        backgroundColor: '#ffffff',
        zIndex: 50
      }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            backgroundColor: '#003087',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1.25rem'
          }}>
            P
          </div>
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#003087', lineHeight: 1 }}>
              PayPal <span style={{ color: '#0070ba' }}>SubWise</span> AI
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Financial Intelligence &amp; Savings</div>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <button 
            onClick={() => setActiveAudience('individual')} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.95rem', fontWeight: activeAudience === 'individual' ? 700 : 500, color: activeAudience === 'individual' ? '#0070ba' : '#475569' }}
          >
            For Individuals
          </button>
          <button 
            onClick={() => setActiveAudience('household')} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.95rem', fontWeight: activeAudience === 'household' ? 700 : 500, color: activeAudience === 'household' ? '#0070ba' : '#475569' }}
          >
            For Households
          </button>
          <button 
            onClick={() => setActiveAudience('business')} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.95rem', fontWeight: activeAudience === 'business' ? 700 : 500, color: activeAudience === 'business' ? '#0070ba' : '#475569' }}
          >
            For Small Businesses
          </button>
        </nav>

        {/* Auth Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link to="/login" className="btn-fintech btn-fintech-outline" style={{ padding: '0.5rem 1.15rem', fontSize: '0.9rem' }}>
            Sign In
          </Link>
          <Link to={`/register?type=${activeAudience}`} className="btn-fintech btn-fintech-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.9rem' }}>
            Get Started Free
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        padding: '5rem 2rem 4rem',
        maxWidth: '1240px',
        margin: '0 auto',
        textAlign: 'center'
      }}>
        {/* Core Product Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.6rem',
          backgroundColor: '#eff6ff',
          color: '#0070ba',
          padding: '0.5rem 1.25rem',
          borderRadius: '9999px',
          fontSize: '0.9rem',
          fontWeight: 700,
          marginBottom: '1.75rem',
          border: '1px solid #bfdbfe'
        }}>
          <Sparkles size={16} /> Don't Just Track Spending. Uncover Real Savings.
        </div>

        {/* Hero Headline */}
        <h1 style={{
          fontSize: '3.5rem',
          fontWeight: 800,
          lineHeight: '1.15',
          letterSpacing: '-0.035em',
          color: '#0f172a',
          maxWidth: '960px',
          margin: '0 auto 1.5rem'
        }}>
          Know Where Your Money Goes. <br />
          <span style={{ color: '#0070ba', background: 'linear-gradient(135deg, #0070ba 0%, #003087 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Discover Where You Can Save.
          </span>
        </h1>

        <p style={{
          fontSize: '1.25rem',
          color: '#475569',
          maxWidth: '780px',
          margin: '0 auto 2.5rem',
          lineHeight: '1.6'
        }}>
          Powered by PayPal financial intelligence. Stop silent subscription creep, compare grocery &amp; vendor prices, catch utility anomalies, and extend your personal or business runway.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.25rem', flexWrap: 'wrap', marginBottom: '3.5rem' }}>
          <Link to={`/register?type=${activeAudience}`} className="btn-fintech btn-fintech-primary btn-lg" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.85rem 2rem', fontSize: '1.05rem', borderRadius: '8px' }}>
            <span>Start Free Transformation</span>
            <ArrowRight size={19} />
          </Link>
          <Link to="/login" className="btn-fintech btn-fintech-outline btn-lg" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.85rem 1.75rem', fontSize: '1.05rem', borderRadius: '8px' }}>
            <span>Explore Live Demo Data</span>
          </Link>
        </div>

        {/* Trust Badges */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '2.5rem', color: '#64748b', fontSize: '0.85rem', fontWeight: 600, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <ShieldCheck size={18} color="#059669" />
            <span>PayPal Sandbox &amp; OAuth 2.0 Certified</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <Lock size={18} color="#0284c7" />
            <span>Bank-Grade TLS 1.3 Encryption</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <CheckCircle2 size={18} color="#7c3aed" />
            <span>Strict Profile Data Isolation</span>
          </div>
        </div>
      </section>

      {/* 3-Audience Interactive Showcase Section */}
      <section style={{ backgroundColor: '#f8fafc', padding: '5rem 2rem', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem' }}>
              Built for Every Stage of Financial Decision-Making
            </h2>
            <p style={{ fontSize: '1.1rem', color: '#64748b', maxWidth: '650px', margin: '0 auto' }}>
              Select your profile type to see tailored intelligence engineered to protect your wallet and optimize your cash.
            </p>

            {/* Audience Tabs */}
            <div style={{
              display: 'inline-flex',
              background: '#ffffff',
              padding: '0.4rem',
              borderRadius: '12px',
              border: '1.5px solid #cbd5e1',
              marginTop: '2rem',
              gap: '0.5rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.04)'
            }}>
              <button
                onClick={() => setActiveAudience('individual')}
                style={{
                  padding: '0.65rem 1.5rem',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                  backgroundColor: activeAudience === 'individual' ? '#0070ba' : 'transparent',
                  color: activeAudience === 'individual' ? '#ffffff' : '#64748b'
                }}
              >
                <User size={18} />
                <span>Individual User</span>
              </button>

              <button
                onClick={() => setActiveAudience('household')}
                style={{
                  padding: '0.65rem 1.5rem',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                  backgroundColor: activeAudience === 'household' ? '#0070ba' : 'transparent',
                  color: activeAudience === 'household' ? '#ffffff' : '#64748b'
                }}
              >
                <Home size={18} />
                <span>Household &amp; Family</span>
              </button>

              <button
                onClick={() => setActiveAudience('business')}
                style={{
                  padding: '0.65rem 1.5rem',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                  backgroundColor: activeAudience === 'business' ? '#0070ba' : 'transparent',
                  color: activeAudience === 'business' ? '#ffffff' : '#64748b'
                }}
              >
                <Building2 size={18} />
                <span>Small Business (SMB)</span>
              </button>
            </div>
          </div>

          {/* Active Audience Content Card */}
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '1.5px solid #e2e8f0',
            padding: '3rem',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05)'
          }}>
            {activeAudience === 'individual' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '3rem', alignItems: 'center' }}>
                <div>
                  <div style={{ color: '#0070ba', fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                    Personal Finance &amp; Subscriptions
                  </div>
                  <h3 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginBottom: '1rem', lineHeight: 1.25 }}>
                    Stop Unconscious Spending. Keep More of Every Paycheck.
                  </h3>
                  <p style={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
                    Personal financial health is eroded not by big one-time purchases, but by forgotten monthly $15–$30 subscriptions and untracked impulse checkouts. SubWise AI audits your PayPal history to eliminate subscription bloat and maximize your discretionary savings.
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Zombie Subscription Detection:</strong> Automatically flags streaming services, apps, and gym passes you haven't engaged with.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Merchant Spending Intelligence:</strong> Identifies which coffee shops, delivery apps, and online retailers claim the biggest share of your income.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Personal Savings Directives:</strong> Actionable steps to pocket an extra $150–$350 each month without sacrificing lifestyle quality.
                      </div>
                    </div>
                  </div>

                  <Link to="/register?type=individual" className="btn-fintech btn-fintech-primary" style={{ padding: '0.75rem 1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>Create Individual Account</span>
                    <ChevronRight size={18} />
                  </Link>
                </div>

                {/* Individual Mock Card */}
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Personal Cash Intelligence</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>$3,420 / mo Net Income</div>
                    </div>
                    <div style={{ background: '#ecfdf5', color: '#059669', padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700 }}>
                      +18% Savings Buffer
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>!</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Cloud Storage Pro ($19.99/mo)</div>
                          <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>Redundant with personal Google Drive</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $240/yr</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>♫</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Spotify Individual ($11.99/mo)</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Switch to Duo/Family shared plan</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $60/yr</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#fef3c7', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>🍔</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Food Delivery Surcharges</div>
                          <div style={{ fontSize: '0.75rem', color: '#d97706' }}>$142 spent in service fees this month</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $110/mo</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeAudience === 'household' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '3rem', alignItems: 'center' }}>
                <div>
                  <div style={{ color: '#0070ba', fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                    Household &amp; Family Management
                  </div>
                  <h3 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginBottom: '1rem', lineHeight: 1.25 }}>
                    Master Groceries, Utilities &amp; Shared Living Costs.
                  </h3>
                  <p style={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
                    Managing a family or shared household requires keeping track of groceries, fluctuating electricity and water bills, broadband, and overlapping family streaming plans. SubWise AI compares vendor prices and keeps shared living costs strictly within budget.
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Grocery Store Price Benchmarking:</strong> Compare shopping spend across regional supermarkets and discover bulk savings.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Utility Bill Anomaly Alerts:</strong> Detect unseasonal electricity, heating, or water surges before billing cycles end.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Family Subscription Consolidation:</strong> Merge duplicate Netflix, YouTube Premium, and Amazon Prime accounts into single household pools.
                      </div>
                    </div>
                  </div>

                  <Link to="/register?type=household" className="btn-fintech btn-fintech-primary" style={{ padding: '0.75rem 1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>Create Household Account</span>
                    <ChevronRight size={18} />
                  </Link>
                </div>

                {/* Household Mock Card */}
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Household Monthly Expense Pool</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>$2,850 Total Shared Outflow</div>
                    </div>
                    <div style={{ background: '#eff6ff', color: '#0070ba', padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700 }}>
                      4 Family Members
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>🛒</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Grocery Optimization Alert</div>
                          <div style={{ fontSize: '0.75rem', color: '#059669' }}>Costco bulk staples vs Local Supermarket</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $185/mo</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>⚡</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Electric Utility Surge Detected</div>
                          <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>+$64 vs same period last year</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#d97706' }}>Inspect Peak Hours</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#f5f3ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>📺</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Duplicate Streaming Accounts</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>2 separate YouTube Premium subscriptions found</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $168/yr</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeAudience === 'business' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '3rem', alignItems: 'center' }}>
                <div>
                  <div style={{ color: '#0070ba', fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                    Small Business &amp; SaaS Solvency
                  </div>
                  <h3 style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginBottom: '1rem', lineHeight: 1.25 }}>
                    Protect Operating Runway from Silent Software Creep.
                  </h3>
                  <p style={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
                    Connecting directly to your PayPal Sandbox or Live account, SubWise AI forecasts real operating cash runway, performs deterministic stress simulations, detects unauthorized license seat inflation, and audits software renewals before payment triggers.
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Live PayPal Reporting Sync:</strong> Automatically reconciles incoming customer revenues and outgoing software disbursements.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Deterministic Runway Modeling:</strong> Exact depletion horizons across baseline, conservative, and stressed states.
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <strong style={{ color: '#0f172a' }}>Tiered Tool Rationalization:</strong> Rank subscriptions by criticality and identify redundant team software stacks.
                      </div>
                    </div>
                  </div>

                  <Link to="/register?type=business" className="btn-fintech btn-fintech-primary" style={{ padding: '0.75rem 1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>Create Business Profile</span>
                    <ChevronRight size={18} />
                  </Link>
                </div>

                {/* Business Mock Card */}
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>PayPal Operating Runway</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>14.2 Months Liquidity</div>
                    </div>
                    <div style={{ background: '#ecfdf5', color: '#059669', padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700 }}>
                      Healthy Buffer
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>!</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>SaaS Price Creep Detected</div>
                          <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>CloudSoft renewed at +$20 higher rate</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#dc2626' }}>Audit Bill</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#eff6ff', color: '#0070ba', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>⚙</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Tool Overlap: Asana vs Notion</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Team using both for task management</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Save $480/yr</span>
                    </div>

                    <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '34px', height: '34px', borderRadius: '6px', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>✓</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>PayPal Sandbox Cash Buffer</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>$4,964.41 verified liquid balance</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>Synchronized</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Interactive Savings Estimator Widget */}
      <section style={{ padding: '5rem 2rem', maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <span style={{ backgroundColor: '#ecfdf5', color: '#059669', padding: '0.35rem 1rem', borderRadius: '9999px', fontSize: '0.85rem', fontWeight: 700 }}>
            Interactive Savings Calculator
          </span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#0f172a', marginTop: '0.75rem', marginBottom: '0.5rem' }}>
            Calculate Your Untapped Savings Potential
          </h2>
          <p style={{ color: '#64748b', fontSize: '1.05rem' }}>
            Adjust your estimated monthly spending to see how much SubWise AI can help you reclaim every year.
          </p>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1.5px solid #cbd5e1',
          padding: '2.5rem',
          display: 'grid',
          gridTemplateColumns: '1.2fr 0.9fr',
          gap: '3rem',
          boxShadow: '0 10px 30px rgba(0,0,0,0.06)'
        }}>
          {/* Sliders Side */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Slider 1: Subscriptions */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <label style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Layers size={17} color="#0070ba" /> Monthly Subscriptions &amp; Digital Services
                </label>
                <span style={{ fontWeight: 800, color: '#0070ba', fontSize: '1.1rem' }}>${subSpend}/mo</span>
              </div>
              <input
                type="range"
                min="20"
                max="800"
                step="10"
                value={subSpend}
                onChange={(e) => setSubSpend(Number(e.target.value))}
                style={{ width: '100%', cursor: 'pointer', accentColor: '#0070ba' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                <span>$20</span>
                <span>$400</span>
                <span>$800+</span>
              </div>
            </div>

            {/* Slider 2: Groceries & Retail */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <label style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShoppingCart size={17} color="#059669" /> Monthly Groceries, Food &amp; Retail
                </label>
                <span style={{ fontWeight: 800, color: '#059669', fontSize: '1.1rem' }}>${grocerySpend}/mo</span>
              </div>
              <input
                type="range"
                min="100"
                max="2500"
                step="50"
                value={grocerySpend}
                onChange={(e) => setGrocerySpend(Number(e.target.value))}
                style={{ width: '100%', cursor: 'pointer', accentColor: '#059669' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                <span>$100</span>
                <span>$1,250</span>
                <span>$2,500+</span>
              </div>
            </div>

            {/* Slider 3: Utilities & Telecom */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <label style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Zap size={17} color="#d97706" /> Monthly Utilities, Internet &amp; Telecom
                </label>
                <span style={{ fontWeight: 800, color: '#d97706', fontSize: '1.1rem' }}>${utilitySpend}/mo</span>
              </div>
              <input
                type="range"
                min="50"
                max="1200"
                step="25"
                value={utilitySpend}
                onChange={(e) => setUtilitySpend(Number(e.target.value))}
                style={{ width: '100%', cursor: 'pointer', accentColor: '#d97706' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                <span>$50</span>
                <span>$600</span>
                <span>$1,200+</span>
              </div>
            </div>
          </div>

          {/* Result Card */}
          <div style={{
            backgroundColor: '#002c6c',
            color: '#ffffff',
            borderRadius: '12px',
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: '#93c5fd', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                Projected AI Savings
              </div>
              <div style={{ fontSize: '2.75rem', fontWeight: 800, color: '#ffffff', lineHeight: 1.1 }}>
                ${estimatedAnnualSavings.toLocaleString()}
                <span style={{ fontSize: '1.1rem', fontWeight: 500, color: '#93c5fd' }}> / year</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '0.75rem', lineHeight: 1.5 }}>
                Conservative estimate based on zombie subscription elimination, vendor price benchmarking, and peak utility optimization.
              </p>
            </div>

            <div style={{ borderTop: '1px solid rgba(255,255,255,0.15)', paddingTop: '1.25rem', marginTop: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', color: '#93c5fd' }}>3-Year Wealth Acceleration:</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8' }}>${threeYearAccumulated.toLocaleString()}</span>
              </div>
              <Link to={`/register?type=${activeAudience}`} className="btn-fintech btn-fintech-primary" style={{ width: '100%', textAlign: 'center', padding: '0.75rem', fontSize: '0.95rem', fontWeight: 700, display: 'block', backgroundColor: '#0070ba' }}>
                Claim Your Savings Now
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison: Traditional Ledgers vs SubWise AI */}
      <section style={{ backgroundColor: '#f8fafc', padding: '5rem 2rem', borderTop: '1px solid #e2e8f0' }}>
        <div style={{ maxWidth: '1050px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem' }}>
              Why Ordinary Bank Statements Leave You In The Dark
            </h2>
            <p style={{ fontSize: '1.05rem', color: '#64748b' }}>
              Historical statements show money you've already lost. SubWise AI gives you the foresight and recommendations to prevent loss.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
            <div style={{
              backgroundColor: '#ffffff',
              border: '1.5px solid #fecaca',
              borderRadius: '14px',
              padding: '2.25rem',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.05)'
            }}>
              <div style={{ color: '#dc2626', fontWeight: 800, fontSize: '1.15rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={22} /> Traditional Bank &amp; PayPal Statements
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.95rem', color: '#475569', padding: 0 }}>
                <li>❌ Backward-looking: Only reports outflow after money has already cleared.</li>
                <li>❌ Blind to silent recurring charges that inflate by $5–$20 year-over-year.</li>
                <li>❌ Fails to compare stores: Doesn't tell you Walmart is 18% cheaper than Target for your staples.</li>
                <li>❌ Ignores utility spikes until your bank account takes the hit.</li>
                <li>❌ Provides zero concrete advice on how to renegotiate or cancel unnecessary services.</li>
              </ul>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              border: '1.5px solid #a7f3d0',
              borderRadius: '14px',
              padding: '2.25rem',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.08)'
            }}>
              <div style={{ color: '#059669', fontWeight: 800, fontSize: '1.15rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={22} /> PayPal SubWise AI Financial Assistant
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.95rem', color: '#334155', padding: 0 }}>
                <li>✓ <strong>Predictive &amp; Prescriptive:</strong> Simulates future cash balances before bills hit.</li>
                <li>✓ <strong>Price Creep Sentinel:</strong> Automatically detects supplier price hikes and seat creep.</li>
                <li>✓ <strong>Smart Store &amp; Vendor Benchmarks:</strong> Pinpoints cheaper alternatives for repeat purchases.</li>
                <li>✓ <strong>Multi-Account Adaptability:</strong> Custom financial engines for Individuals, Households, and SMBs.</li>
                <li>✓ <strong>Automated Renegotiation Drafts:</strong> AI writes supplier dispute letters and rate-reduction requests.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        marginTop: 'auto',
        borderTop: '1px solid #e2e8f0',
        padding: '3rem 2rem 2rem',
        backgroundColor: '#ffffff',
        textAlign: 'center',
        fontSize: '0.85rem',
        color: '#64748b'
      }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#003087', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem' }}>P</div>
            <strong style={{ color: '#003087', fontSize: '1rem' }}>PayPal SubWise AI</strong>
          </div>
          <div style={{ display: 'flex', gap: '2rem', fontSize: '0.85rem' }}>
            <Link to={`/register?type=${activeAudience}`} style={{ color: '#64748b', textDecoration: 'none' }}>Get Started</Link>
            <Link to="/login" style={{ color: '#64748b', textDecoration: 'none' }}>Sign In</Link>
            <Link to="/login" style={{ color: '#64748b', textDecoration: 'none' }}>Demo Sandbox</Link>
          </div>
        </div>
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
          PayPal SubWise AI — Your AI-Powered Financial Intelligence and Savings Assistant. Designed for individual, household, and small business financial resilience.
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
