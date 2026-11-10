import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { intelligenceAPI } from '../services/api';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Info,
  DollarSign,
  Calendar,
  BarChart2,
  Layers,
  Target,
} from 'lucide-react';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const CATEGORY_COLORS = [
  '#0070ba', '#00457c', '#6366f1', '#8b5cf6', '#06b6d4',
  '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#64748b',
];

const ratingStyle = (rating) => {
  if (!rating) return { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' };
  const r = rating.toLowerCase();
  if (r.includes('excellent')) return { bg: '#ecfdf5', color: '#059669', border: '#a7f3d0' };
  if (r.includes('good')) return { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' };
  if (r.includes('fair')) return { bg: '#fef3c7', color: '#d97706', border: '#fde68a' };
  return { bg: '#fee2e2', color: '#b91c1c', border: '#fca5a5' };
};

// ─── Health Score Gauge ───────────────────────────────────────────────────────
const HealthScoreGauge = ({ score, rating }) => {
  const style = ratingStyle(rating);
  const circumference = 2 * Math.PI * 52;
  const progress = (score / 100) * circumference;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.65rem' }}>
      <div style={{ position: 'relative', width: '140px', height: '140px' }}>
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r="52" fill="none" stroke="#e2e8f0" strokeWidth="12" />
          <circle
            cx="70" cy="70" r="52"
            fill="none"
            stroke={style.color}
            strokeWidth="12"
            strokeDasharray={`${progress} ${circumference}`}
            strokeLinecap="round"
            transform="rotate(-90 70 70)"
            style={{ transition: 'stroke-dasharray 0.8s ease' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: style.color, lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748b' }}>/ 100</div>
        </div>
      </div>
      <span style={{
        fontSize: '0.82rem', fontWeight: 700, padding: '0.25rem 0.8rem',
        borderRadius: '99px', background: style.bg, color: style.color, border: `1px solid ${style.border}`,
      }}>
        {rating || 'N/A'}
      </span>
    </div>
  );
};

// ─── Section Heading ──────────────────────────────────────────────────────────
const SectionHeading = ({ icon: Icon, title, subtitle, linkTo, linkLabel }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
        <Icon size={18} color="#0070ba" />
        <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>{title}</h2>
      </div>
      {subtitle && <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>{subtitle}</p>}
    </div>
    {linkTo && (
      <Link to={linkTo} style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0070ba', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem', whiteSpace: 'nowrap' }}>
        {linkLabel || 'View all'} <ArrowRight size={13} />
      </Link>
    )}
  </div>
);

// ─── Loading State ────────────────────────────────────────────────────────────
const LoadingCard = () => (
  <div style={{ padding: '2.5rem', textAlign: 'center', color: '#64748b' }}>
    <RefreshCw size={24} className="spin-icon" color="#0070ba" />
    <div style={{ marginTop: '0.75rem', fontSize: '0.88rem' }}>Loading financial intelligence...</div>
  </div>
);

// ─── Error Banner ─────────────────────────────────────────────────────────────
const ErrorBanner = ({ message }) => (
  <div style={{ padding: '1rem 1.25rem', background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '10px', fontSize: '0.88rem', color: '#92400e', display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
    <AlertTriangle size={16} /> {message}
  </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────
const InsightsPage = () => {
  const { business } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('health');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await intelligenceAPI.getUnified();
        setData(result);
      } catch (err) {
        const msg = err?.response?.data?.detail || 'Failed to load financial insights. Please try again.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const spending = data?.spending_analysis;
  const health = data?.health_score;
  const recs = data?.recommendations || [];
  const forecast = data?.forecast;

  // Build chart data for spending (top_categories is List[Dict])
  const categoryChartData = spending?.top_categories
    ? spending.top_categories.map((c) => ({
        name: c.category || c.name || 'Other',
        current: c.current_month_amount || c.amount || 0,
        prior: c.prior_month_amount || 0,
      }))
    : [];

  const pieData = spending?.top_categories
    ? spending.top_categories.map((c) => ({
        name: c.category || c.name || 'Other',
        value: c.current_month_amount || c.amount || 0,
      }))
    : [];

  // Forecast: timeline is [{day, date, baseline_cash, conservative_cash, optimistic_cash}]
  const forecastChartData = forecast?.timeline
    ? forecast.timeline.map((pt) => ({
        day: pt.day,
        baseline: pt.baseline_cash,
        conservative: pt.conservative_cash,
        optimistic: pt.optimistic_cash,
      }))
    : [];

  // Day snapshots
  const forecastSnapshots = forecast
    ? [
        { label: 'Day 30 (Baseline)', balance: forecast.day_30_balance?.baseline },
        { label: 'Day 60 (Baseline)', balance: forecast.day_60_balance?.baseline },
        { label: 'Day 90 (Baseline)', balance: forecast.day_90_balance?.baseline },
      ]
    : [];

  const sections = [
    { id: 'health', label: 'Financial Health', icon: ShieldCheck },
    { id: 'spending', label: 'Spending Analytics', icon: BarChart2 },
    { id: 'recommendations', label: 'AI Recommendations', icon: Sparkles },
    { id: 'forecast', label: 'Forecast Preview', icon: TrendingUp },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
            background: '#f5f3ff', color: '#7c3aed', padding: '0.3rem 0.8rem',
            borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem',
          }}>
            <Activity size={13} /> AI Financial Intelligence
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.3rem', lineHeight: 1.25 }}>
            Financial Insights
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
            Unified financial intelligence: health score, spending trends, savings recommendations, and 90-day forecast
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
          <Link to="/savings-discovery" className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.88rem', minHeight: '40px', padding: '0.45rem 1rem' }}>
            <Sparkles size={14} /> Savings Discovery
          </Link>
          <Link to="/assistant" className="btn-fintech btn-fintech-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.88rem', minHeight: '40px', padding: '0.45rem 1rem' }}>
            Ask AI Assistant <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Section Nav Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', borderBottom: '2px solid #e2e8f0', paddingBottom: '0' }}>
        {sections.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveSection(id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.6rem 1rem',
              border: 'none',
              background: 'none',
              color: activeSection === id ? '#0070ba' : '#64748b',
              fontWeight: activeSection === id ? 800 : 600,
              fontSize: '0.87rem',
              cursor: 'pointer',
              borderBottom: activeSection === id ? '2.5px solid #0070ba' : '2.5px solid transparent',
              marginBottom: '-2px',
              transition: 'all 0.15s ease',
            }}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="fintech-card"><LoadingCard /></div>
      ) : error ? (
        <ErrorBanner message={error} />
      ) : (
        <>
          {/* ── HEALTH SCORE ─────────────────────────────────────────────── */}
          {activeSection === 'health' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                <SectionHeading
                  icon={ShieldCheck}
                  title="Financial Health Score"
                  subtitle="Composite 4-factor wellness assessment grounded in your actual spending data"
                />

                {health ? (
                  <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
                    <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.65rem' }}>
                      <HealthScoreGauge score={health.score ?? health.overall_score ?? 0} rating={health.rating} />
                      <div style={{ fontSize: '0.78rem', color: '#64748b', textAlign: 'center', maxWidth: '160px' }}>
                        {health.disclaimer || 'Not a credit score. Deterministic assessment only.'}
                      </div>
                    </div>

                    <div style={{ flex: 1, minWidth: '240px' }}>
                      {/* Factor breakdown */}
                      {health.factors && health.factors.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
                          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.25rem' }}>
                            Factor Breakdown
                          </div>
                          {health.factors.map((f, i) => (
                            <div key={i}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.25rem' }}>
                                <span style={{ fontWeight: 600, color: '#374151' }}>{f.factor_name || f.name}</span>
                                <span style={{ fontWeight: 800, color: '#0f172a' }}>{f.score}/{f.max_score}</span>
                              </div>
                              <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '99px', overflow: 'hidden' }}>
                                <div style={{
                                  height: '100%',
                                  width: `${(f.score / f.max_score) * 100}%`,
                                  background: f.score / f.max_score >= 0.7 ? '#10b981' : f.score / f.max_score >= 0.4 ? '#f59e0b' : '#ef4444',
                                  borderRadius: '99px',
                                  transition: 'width 0.6s ease',
                                }} />
                              </div>
                              {(f.description || f.explanation) && (
                                <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>{f.description || f.explanation}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Positive highlights */}
                      {health.positive_highlights && health.positive_highlights.length > 0 && (
                        <div style={{ marginBottom: '0.75rem' }}>
                          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#059669', marginBottom: '0.4rem' }}>✓ Strengths</div>
                          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            {health.positive_highlights.map((h, i) => (
                              <li key={i} style={{ fontSize: '0.82rem', color: '#374151', display: 'flex', gap: '0.4rem', alignItems: 'flex-start' }}>
                                <CheckCircle2 size={13} color="#059669" style={{ flexShrink: 0, marginTop: '1px' }} /> {h}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Risk factors */}
                      {health.risk_factors && health.risk_factors.length > 0 && (
                        <div>
                          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#d97706', marginBottom: '0.4rem' }}>⚠ Risk Factors</div>
                          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            {health.risk_factors.map((r, i) => (
                              <li key={i} style={{ fontSize: '0.82rem', color: '#374151', display: 'flex', gap: '0.4rem', alignItems: 'flex-start' }}>
                                <AlertTriangle size={13} color="#d97706" style={{ flexShrink: 0, marginTop: '1px' }} /> {r}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.88rem' }}>
                    Add expenses and income to generate your financial health score.
                  </div>
                )}
              </div>

              {/* Actionable Steps */}
              {((health?.actionable_improvements && health.actionable_improvements.length > 0) || (health?.actionable_steps && health.actionable_steps.length > 0)) && (
                <div className="fintech-card" style={{ padding: '1.5rem 2rem' }}>
                  <div style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
                    Recommended Actions
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
                    {(health.actionable_improvements || health.actionable_steps).map((step, i) => (
                      <div key={i} style={{ padding: '0.85rem 1rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '0.85rem', color: '#374151', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                        <span style={{ fontWeight: 800, color: '#0070ba', flexShrink: 0 }}>{i + 1}.</span>
                        {step}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── SPENDING ANALYTICS ────────────────────────────────────────── */}
          {activeSection === 'spending' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {spending && spending.has_sufficient_data ? (
                <>
                  {/* Category Bar Chart */}
                  <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                    <SectionHeading
                      icon={BarChart2}
                      title="Category Spending — Month-over-Month"
                      subtitle="Current vs prior month spending by category"
                    />
                    {categoryChartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={categoryChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                          <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={(v) => `$${v}`} />
                          <Tooltip formatter={(v) => fmt(v)} />
                          <Legend />
                          <Bar dataKey="prior" name="Prior Month" fill="#bfdbfe" radius={[3, 3, 0, 0]} />
                          <Bar dataKey="current" name="Current Month" fill="#0070ba" radius={[3, 3, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.88rem' }}>No category data available.</div>
                    )}
                  </div>

                  {/* Pie + Spikes */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
                    {/* Pie */}
                    <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                      <div style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--navy-slate)', marginBottom: '1rem' }}>
                        Spending Distribution
                      </div>
                      {pieData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={220}>
                          <PieChart>
                            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                              {pieData.map((_, i) => (
                                <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(v) => fmt(v)} />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.88rem' }}>No data.</div>
                      )}
                    </div>

                    {/* Unusual Spikes */}
                    <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                      <div style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--navy-slate)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <AlertTriangle size={15} color="#d97706" /> Spending Spikes Detected
                      </div>
                      {spending.unusual_spikes && spending.unusual_spikes.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                          {spending.unusual_spikes.map((sp, i) => (
                            <div key={i} style={{ padding: '0.85rem 1rem', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px' }}>
                              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#92400e', marginBottom: '0.2rem' }}>
                                {typeof sp === 'string' ? sp : (sp.category || 'Spike Alert')}
                              </div>
                              {typeof sp === 'object' && sp.description && (
                                <div style={{ fontSize: '0.8rem', color: '#78350f' }}>{sp.description}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                          <CheckCircle2 size={20} color="#10b981" style={{ marginBottom: '0.4rem' }} />
                          <div>No unusual spending spikes detected this month.</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Savings Rate */}
                  {(spending.savings_rate_percent !== undefined || spending.savings_rate !== undefined) && (
                    <div className="fintech-card" style={{ padding: '1.25rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                      <div>
                        <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#64748b', marginBottom: '0.2rem' }}>Current Savings Rate</div>
                        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: (spending.savings_rate_percent ?? spending.savings_rate) >= 20 ? '#059669' : (spending.savings_rate_percent ?? spending.savings_rate) >= 10 ? '#d97706' : '#b91c1c' }}>
                          {(spending.savings_rate_percent ?? spending.savings_rate).toFixed(1)}%
                        </div>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#64748b', maxWidth: '320px', lineHeight: 1.5 }}>
                        {(spending.savings_rate_percent ?? spending.savings_rate) >= 20
                          ? '🎉 Excellent! You are meeting or exceeding the recommended 20% savings target.'
                          : (spending.savings_rate_percent ?? spending.savings_rate) >= 10
                          ? '📊 Fair savings rate. Target 20% by reducing discretionary and subscription spend.'
                          : '⚠️ Low savings rate. Review your top spending categories and subscription commitments.'}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="fintech-card" style={{ padding: '2.5rem', textAlign: 'center' }}>
                  <BarChart2 size={36} color="#cbd5e1" strokeWidth={1.5} style={{ marginBottom: '0.75rem' }} />
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: '#475569', marginBottom: '0.4rem' }}>Insufficient Data</div>
                  <div style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: '1.25rem' }}>
                    {spending?.notes || 'Add at least one month of expenses to see spending analytics.'}
                  </div>
                  <Link to="/expenses" className="btn-fintech btn-fintech-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.88rem', minHeight: '38px' }}>
                    Add Expenses <ArrowRight size={14} />
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* ── RECOMMENDATIONS ───────────────────────────────────────────── */}
          {activeSection === 'recommendations' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                <SectionHeading
                  icon={Sparkles}
                  title="AI Savings Recommendations"
                  subtitle="Actionable suggestions based on your actual spending patterns"
                  linkTo="/savings-discovery"
                  linkLabel="Vendor comparison"
                />
                {recs.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
                    {recs.map((rec, i) => (
                      <div key={i} style={{
                        padding: '1.15rem', background: '#f8fafc',
                        border: '1px solid #e2e8f0', borderRadius: '10px',
                        display: 'flex', flexDirection: 'column', gap: '0.5rem',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a', lineHeight: 1.3 }}>{rec.title}</div>
                          {rec.monthly_savings > 0 && (
                            <span style={{ fontSize: '0.78rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: '#ecfdf5', color: '#059669', flexShrink: 0 }}>
                              Save {fmt(rec.monthly_savings)}/mo
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.5 }}>{rec.explanation || rec.description}</div>
                        {(rec.recommended_action || (rec.action_items && rec.action_items[0])) && (
                          <div style={{ fontSize: '0.78rem', color: '#0070ba', fontWeight: 600, marginTop: '0.2rem' }}>
                            → {rec.recommended_action || rec.action_items[0]}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.88rem' }}>
                    No recommendations available yet. Add expenses to generate personalized suggestions.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── FORECAST ──────────────────────────────────────────────────── */}
          {activeSection === 'forecast' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
                <SectionHeading
                  icon={TrendingUp}
                  title="90-Day Financial Forecast"
                  subtitle="Three-scenario projection: Baseline, Conservative (−15% income / +15% spend), and Optimistic (+5% income / −12% spend)"
                />
                {forecastChartData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={forecastChartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#64748b' }} label={{ value: 'Day', position: 'insideBottomRight', offset: -5, fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                        <Tooltip formatter={(v) => fmt(v)} />
                        <Legend />
                        <Line type="monotone" dataKey="baseline" stroke="#0070ba" strokeWidth={2.5} dot={false} name="Baseline" />
                        <Line type="monotone" dataKey="conservative" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="5 3" dot={false} name="Conservative" />
                        <Line type="monotone" dataKey="optimistic" stroke="#10b981" strokeWidth={1.5} strokeDasharray="3 2" dot={false} name="Optimistic" />
                      </LineChart>
                    </ResponsiveContainer>

                    {/* Day-30/60/90 Snapshots */}
                    {forecastSnapshots && forecastSnapshots.length > 0 && (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginTop: '1.25rem' }}>
                        {forecastSnapshots.map((snap, i) => (
                          <div key={i} style={{ padding: '0.85rem 1rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', marginBottom: '0.25rem', textTransform: 'uppercase' }}>{snap.label}</div>
                            <div style={{ fontWeight: 800, fontSize: '1.1rem', color: (snap.balance || 0) >= 0 ? '#059669' : '#b91c1c' }}>
                              {fmt(snap.balance || 0)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.5 }}>
                      Forecast is a deterministic projection based on your recorded income, expenses, and known recurring subscriptions.
                      It is not financial advice and does not account for unexpected income changes or one-time expenses.
                    </div>
                  </>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.88rem' }}>
                    <TrendingUp size={32} color="#cbd5e1" strokeWidth={1.5} style={{ marginBottom: '0.75rem' }} />
                    <div style={{ fontWeight: 700, color: '#475569', marginBottom: '0.4rem' }}>Forecast requires income and expense data</div>
                    <div style={{ marginBottom: '1.25rem' }}>Add your monthly income and at least one month of expenses to generate a 90-day forecast.</div>
                    <Link to="/expenses" className="btn-fintech btn-fintech-primary"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.88rem', minHeight: '38px' }}>
                      Record Expenses <ArrowRight size={14} />
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default InsightsPage;
