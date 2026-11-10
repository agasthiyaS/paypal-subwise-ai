import React, { useState, useEffect, useMemo } from 'react';
import { subscriptionsAPI, paypalAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { TierBadge, StatusBadge } from '../components/common/Badge';
import {
  Search,
  Filter,
  Layers,
  AlertTriangle,
  Zap,
  TrendingUp,
  RefreshCw,
  Database,
  DollarSign,
  Calendar,
  BarChart3,
  TrendingDown,
  CheckCircle2,
  Clock
} from 'lucide-react';

const SubscriptionsPage = () => {
  const { business, refreshBusiness } = useAuth();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [summary, setSummary] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);

  // Active view tab
  const [activeTab, setActiveTab] = useState('analysis'); // 'analysis' or 'directory'

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [tierFilter, setTierFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [detectionFilter, setDetectionFilter] = useState('All');

  const loadSubscriptions = async () => {
    try {
      setLoading(true);
      const [subData, analysisData] = await Promise.allSettled([
        subscriptionsAPI.getSubscriptions(),
        subscriptionsAPI.getAnalysis(),
      ]);

      if (subData.status === 'fulfilled') {
        setSummary(subData.value);
        setSubscriptions(subData.value?.subscriptions || []);
      }
      if (analysisData.status === 'fulfilled') {
        setAnalysis(analysisData.value);
      }
    } catch (err) {
      console.error('Failed to load subscriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptions();
  }, [business?.id]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await paypalAPI.sync();
      setSyncStatus({
        type: 'success',
        text: res.message || 'Successfully synchronized PayPal subscriptions.'
      });
      await refreshBusiness();
      await loadSubscriptions();
    } catch (err) {
      setSyncStatus({
        type: 'error',
        text: err.response?.data?.detail || 'PayPal synchronization failed.'
      });
    } finally {
      setSyncing(false);
    }
  };

  // Dynamic filter lists
  const categories = useMemo(() => {
    const set = new Set(subscriptions.map((s) => s.category).filter(Boolean));
    return ['All', ...Array.from(set)];
  }, [subscriptions]);

  const tiers = ['All', 'Tier 1 (Core Ops)', 'Tier 2 (Important)', 'Tier 3 (Discretionary)'];
  const statuses = ['All', 'Active', 'At Risk', 'Redundant', 'Zombie'];
  const detectionTypes = ['All', 'Confirmed', 'Potential', 'Uncertain'];

  const filtered = useMemo(() => {
    return subscriptions.filter((s) => {
      const vendorName = s.vendor_name || s.name || '';
      const matchSearch = vendorName.toLowerCase().includes(search.toLowerCase());
      const matchCat = categoryFilter === 'All' || s.category === categoryFilter;
      const matchTier = tierFilter === 'All' || s.tier === tierFilter;
      const matchStatus = statusFilter === 'All' || (s.status || '').toLowerCase() === statusFilter.toLowerCase();
      const matchDetection = detectionFilter === 'All' || (s.detection_type || 'confirmed').toLowerCase() === detectionFilter.toLowerCase();
      return matchSearch && matchCat && matchTier && matchStatus && matchDetection;
    });
  }, [subscriptions, search, categoryFilter, tierFilter, statusFilter, detectionFilter]);

  const totalFilteredSpend = filtered.reduce((s, sub) => s + (sub.latest_amount || 0), 0);

  const totalSubsCount = summary?.total_active_count ?? subscriptions.length;
  const monthlySaaSSpend = analysis?.total_monthly_commitment ?? (summary?.total_monthly_spend ?? 0.0);
  const annualSaaSSpend = analysis?.total_annual_commitment ?? (summary?.total_annual_spend ?? 0.0);
  const zombieCount = summary?.zombie_count ?? subscriptions.filter(s => s.status === 'zombie').length;
  const redundantCount = summary?.redundant_tool_count ?? subscriptions.filter(s => s.status === 'redundant').length;
  const atRiskCount = summary?.at_risk_count ?? subscriptions.filter(s => s.status === 'at_risk' || (s.price_change_pct || 0) >= 15).length;
  const potentialSavings = summary?.potential_monthly_savings ?? 0.0;

  const selectStyle = {
    padding: '0.55rem 0.85rem',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-surface)',
    fontSize: '0.84rem',
    color: 'var(--text-body)',
    cursor: 'pointer',
    outline: 'none',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.45rem', lineHeight: 1.25 }}>
            Subscription Expense Management
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
            Comprehensive expense analysis, cadence normalization, 7-category breakdown, and recurring commitments
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minHeight: '48px', padding: '0.65rem 1.35rem', fontSize: '1rem' }}
          >
            <RefreshCw size={17} className={syncing ? 'spin-icon' : ''} />
            <span>{syncing ? 'Scanning...' : 'Sync PayPal Subscriptions'}</span>
          </button>
        </div>
      </div>

      {syncStatus && (
        <div style={{
          padding: '0.95rem 1.35rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          background: syncStatus.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: syncStatus.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
          border: `1.5px solid ${syncStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`
        }}>
          {syncStatus.text}
        </div>
      )}

      {/* High-Level Analysis Metric Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
        gap: '1.35rem',
      }}>
        {/* Monthly Commitment */}
        <div className="fintech-card" style={{ padding: '1.45rem 1.65rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Monthly Spend Commitment
            </span>
            <Calendar size={20} color="var(--navy-primary)" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
            ${monthlySaaSSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-muted)' }}>/mo</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
            {analysis?.confirmed_monthly_commitment ? `$${analysis.confirmed_monthly_commitment.toFixed(2)} confirmed` : '0 confirmed'} · {analysis?.potential_monthly_commitment ? `$${analysis.potential_monthly_commitment.toFixed(2)} potential` : '0 potential'}
          </div>
        </div>

        {/* Annual Commitment */}
        <div className="fintech-card" style={{ padding: '1.45rem 1.65rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Estimated Annual Commitments
            </span>
            <DollarSign size={20} color="var(--paypal-blue)" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
            ${annualSaaSSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-muted)' }}>/yr</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
            Historical actual: ${Number(analysis?.actual_historical_spend_total || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} settled
          </div>
        </div>

        {/* Revenue Impact */}
        <div className="fintech-card" style={{
          padding: '1.45rem 1.65rem',
          background: analysis?.revenue_comparison?.has_sufficient_revenue_data
            ? (analysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-bg)' : analysis.revenue_comparison.burden_level === 'moderate' ? 'var(--amber-bg)' : 'var(--rose-bg)')
            : 'var(--bg-surface)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Revenue vs Subscriptions
            </span>
            <TrendingUp size={20} color={analysis?.revenue_comparison?.has_sufficient_revenue_data ? (analysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-dark)' : 'var(--amber-dark)') : 'var(--text-muted)'} />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: analysis?.revenue_comparison?.has_sufficient_revenue_data ? (analysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-dark)' : 'var(--amber-dark)') : 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
            {analysis?.revenue_comparison?.revenue_percentage !== null && analysis?.revenue_comparison?.revenue_percentage !== undefined
              ? `${analysis.revenue_comparison.revenue_percentage}%`
              : 'N/A'}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
            {analysis?.revenue_comparison?.explanation || 'Awaiting operating sales'}
          </div>
        </div>

        {/* Spending Velocity & Alerts */}
        <div className="fintech-card" style={{ padding: '1.45rem 1.65rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Spending Velocity &amp; Trend
            </span>
            <Zap size={20} color="var(--indigo-accent)" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy-slate)', textTransform: 'capitalize' }}>
            {analysis?.spending_trends?.trend_direction ? analysis.spending_trends.trend_direction.replace('_', ' ') : 'Insufficient Data'}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
            {analysis?.spending_trends?.trend_summary || 'Synchronize transactions to analyze spending velocity'}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '2px solid var(--border-light)', paddingBottom: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('analysis')}
          style={{
            padding: '0.65rem 1.35rem',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            fontSize: '0.95rem',
            fontWeight: 700,
            cursor: 'pointer',
            background: activeTab === 'analysis' ? 'var(--navy-primary)' : 'transparent',
            color: activeTab === 'analysis' ? '#fff' : 'var(--text-muted)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem'
          }}
        >
          <BarChart3 size={17} />
          <span>Expense Analysis &amp; Categories</span>
        </button>

        <button
          onClick={() => setActiveTab('directory')}
          style={{
            padding: '0.65rem 1.35rem',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            fontSize: '0.95rem',
            fontWeight: 700,
            cursor: 'pointer',
            background: activeTab === 'directory' ? 'var(--navy-primary)' : 'transparent',
            color: activeTab === 'directory' ? '#fff' : 'var(--text-muted)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem'
          }}
        >
          <Layers size={17} />
          <span>Subscription Directory ({subscriptions.length})</span>
        </button>
      </div>

      {/* TAB 1: EXPENSE ANALYSIS VIEW */}
      {activeTab === 'analysis' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

          {/* Cadence Normalization Rule Banner */}
          <div className="fintech-card" style={{ padding: '1.25rem 1.5rem', background: 'var(--bg-subtle)', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
              <Clock size={18} color="var(--navy-primary)" />
              <span style={{ fontWeight: 700, color: 'var(--navy-slate)', fontSize: '0.95rem' }}>
                Multi-Cadence Frequency Normalization Model
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
              Different SaaS providers bill across varied intervals. SubWise converts each frequency into comparable costs:
              <strong> Weekly</strong> (~4.33× / mo, 52× / yr) ·
              <strong> Monthly</strong> (1× / mo, 12× / yr) ·
              <strong> Quarterly</strong> (÷3 / mo, 4× / yr) ·
              <strong> Annual</strong> (÷12 / mo, 1× / yr).
              Estimated commitments are strictly segregated from actual historical settlements.
            </div>
          </div>

          {/* Category-Wise Analysis Grid (7 Canonical Categories) */}
          <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
                Category-Wise SaaS Commitments
              </h2>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Commitments aggregated across the 7 canonical SaaS domains
              </p>
            </div>

            {(!analysis?.category_analysis || analysis.category_analysis.length === 0 || !analysis.has_subscriptions) ? (
              <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
                No category data available. Synchronize transactions to detect subscriptions.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
                {analysis.category_analysis.map((cat) => {
                  const pct = cat.percentage_of_total || 0;
                  return (
                    <div key={cat.category} style={{
                      padding: '1.15rem 1.35rem',
                      background: cat.monthly_spend > 0 ? 'var(--bg-surface)' : 'var(--bg-subtle)',
                      borderRadius: 'var(--radius-md)',
                      border: `1.5px solid ${cat.monthly_spend > 0 ? 'var(--border-medium)' : 'var(--border-light)'}`,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--navy-slate)' }}>
                            {cat.category}
                          </span>
                          <span style={{ fontSize: '0.78rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: cat.subscription_count > 0 ? 'var(--paypal-blue-subtle)' : 'var(--border-light)', color: cat.subscription_count > 0 ? 'var(--navy-primary)' : 'var(--text-muted)' }}>
                            {cat.subscription_count} {cat.subscription_count === 1 ? 'tool' : 'tools'}
                          </span>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                            ${cat.monthly_spend.toFixed(2)}
                            <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>/mo</span>
                          </div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-primary)' }}>
                            {pct}% of SaaS
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div style={{ height: '6px', background: 'var(--border-light)', borderRadius: '99px', overflow: 'hidden', marginTop: '0.65rem' }}>
                          <div style={{
                            width: `${pct}%`,
                            height: '100%',
                            background: 'var(--navy-primary)',
                            borderRadius: '99px'
                          }} />
                        </div>
                      </div>

                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.85rem' }}>
                        {cat.vendors && cat.vendors.length > 0
                          ? `Providers: ${cat.vendors.join(', ')}`
                          : 'No active subscriptions detected in this category.'}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Vendor-Wise Expense Analysis Table */}
          <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
                Vendor-Wise Commitment &amp; Cadence Analysis
              </h2>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Detailed breakdown per provider with cadence conversion, billing classification, and verified historical settlements
              </p>
            </div>

            {(!analysis?.vendor_analysis || analysis.vendor_analysis.length === 0) ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                No vendor commitments detected yet.
              </div>
            ) : (
              <div className="fintech-table-wrapper">
                <table className="fintech-table">
                  <thead>
                    <tr>
                      <th>Software Provider</th>
                      <th>Category (Canonical)</th>
                      <th>Cadence &amp; Type</th>
                      <th style={{ textAlign: 'right' }}>Billed Amount</th>
                      <th style={{ textAlign: 'right' }}>Monthly Eq.</th>
                      <th style={{ textAlign: 'right' }}>Annual Eq.</th>
                      <th style={{ textAlign: 'right' }}>Historical Spend</th>
                      <th>Status &amp; Alert</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.vendor_analysis.map((v) => (
                      <tr key={v.vendor_name}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                            <span style={{ fontWeight: 700, color: 'var(--navy-slate)', fontSize: '0.92rem' }}>
                              {v.vendor_name}
                            </span>
                            {v.detection_type === 'potential' && (
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a' }}>
                                Potential
                              </span>
                            )}
                            {v.billing_type === 'variable' && (
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                                Variable
                              </span>
                            )}
                          </div>
                          {v.detection_reason && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic', maxWidth: '300px', lineHeight: 1.3 }}>
                              {v.detection_reason}
                            </div>
                          )}
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>
                          {v.standard_category}
                        </td>
                        <td>
                          <div style={{ textTransform: 'capitalize', fontSize: '0.88rem', fontWeight: 600, color: 'var(--navy-slate)' }}>
                            {v.cadence}
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                            {v.billing_type} billing
                          </div>
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                          ${v.latest_amount.toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--navy-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                          ${v.monthly_equivalent.toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'right', color: 'var(--text-body)', fontFamily: 'JetBrains Mono, monospace' }}>
                          ${v.annual_equivalent.toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'right', color: 'var(--emerald-dark)', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
                          ${v.historical_spend_total.toFixed(2)}
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {v.transaction_count} {v.transaction_count === 1 ? 'charge' : 'charges'}
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <span style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              padding: '0.2rem 0.5rem',
                              borderRadius: '4px',
                              display: 'inline-block',
                              textAlign: 'center',
                              background: v.status === 'active' ? 'var(--emerald-bg)' : v.status === 'at_risk' ? 'var(--amber-bg)' : 'var(--rose-bg)',
                              color: v.status === 'active' ? 'var(--emerald-dark)' : v.status === 'at_risk' ? 'var(--amber-dark)' : 'var(--rose-dark)',
                            }}>
                              {v.status.toUpperCase()}
                            </span>
                            {v.price_change_pct >= 10.0 && (
                              <span style={{ fontSize: '0.7rem', color: 'var(--rose-dark)', fontWeight: 700 }}>
                                +{v.price_change_pct}% creep
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Spending Trends & Alerts Section */}
          {analysis?.spending_trends?.price_creep_alerts && analysis.spending_trends.price_creep_alerts.length > 0 && (
            <div className="fintech-card" style={{ padding: '1.5rem', background: 'var(--amber-bg)', border: '1px solid var(--amber-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
                <AlertTriangle size={20} color="var(--amber-dark)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--amber-dark)', margin: 0 }}>
                  Subscription Spending Anomalies &amp; Price Alerts
                </h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {analysis.spending_trends.price_creep_alerts.map((a, idx) => (
                  <div key={idx} style={{ fontSize: '0.88rem', color: 'var(--amber-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>•</span>
                    <span><strong>{a.vendor}:</strong> {a.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}

      {/* TAB 2: DIRECTORY VIEW */}
      {activeTab === 'directory' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Tier Info Bar */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem',
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem',
          }}>
            {[
              { tier: 'Tier 1', label: 'Mission-Critical Core Ops', desc: 'Non-negotiable infrastructure (AWS, GitHub, Google Workspace). Never paused during cash crunches.', color: '#0070ba', bg: '#e0f2fe' },
              { tier: 'Tier 2', label: 'Important Operational Tools', desc: 'CRM, collaboration, monitoring. Subject to seat audits and plan downgrades if revenue dips.', color: '#6366f1', bg: '#eef2ff' },
              { tier: 'Tier 3', label: 'Discretionary / Convenience', desc: 'Convenience tools with alternatives. First in line for freezing during active cash pressure.', color: '#ef4444', bg: '#fef2f2' },
            ].map((t) => (
              <div key={t.tier} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                <div style={{ background: t.bg, color: t.color, padding: '0.3rem 0.6rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.78rem', flexShrink: 0 }}>
                  {t.tier}
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-body)', marginBottom: '0.2rem' }}>{t.label}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{t.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Filters & Search */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ position: 'relative', flex: '1', minWidth: '200px' }}>
              <Search size={15} style={{ position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-caption)' }} />
              <input
                className="form-input"
                placeholder="Search subscriptions or vendor…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ paddingLeft: '2.2rem', width: '100%' }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Filter size={14} color="var(--text-muted)" />
              <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} style={selectStyle}>
                {categories.map((c) => <option key={c}>{c}</option>)}
              </select>
              <select value={tierFilter} onChange={(e) => setTierFilter(e.target.value)} style={selectStyle}>
                {tiers.map((t) => <option key={t}>{t}</option>)}
              </select>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={selectStyle}>
                {statuses.map((s) => <option key={s}>{s}</option>)}
              </select>
              <select value={detectionFilter} onChange={(e) => setDetectionFilter(e.target.value)} style={selectStyle}>
                {detectionTypes.map((d) => <option key={d}>{d === 'All' ? 'All Detections' : d}</option>)}
              </select>
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
              Showing {filtered.length} of {subscriptions.length}
              {filtered.length > 0 && ` · $${totalFilteredSpend.toFixed(2)}/mo filtered`}
            </div>
          </div>

          {/* Directory Table */}
          <div className="fintech-table-wrapper">
            <table className="fintech-table">
              <thead>
                <tr>
                  <th>Subscription</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Monthly Eq.</th>
                  <th>Next Payment</th>
                  <th>Tier</th>
                  <th>Essential</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '3rem 2rem', color: 'var(--text-muted)' }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        background: 'var(--bg-subtle)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 1rem'
                      }}>
                        <Database size={24} color="var(--text-muted)" />
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
                        {subscriptions.length === 0 ? 'No recurring subscriptions detected yet' : 'No subscriptions match your filters'}
                      </div>
                      <div style={{ fontSize: '0.95rem', maxWidth: '460px', margin: '0 auto' }}>
                        {subscriptions.length === 0
                          ? 'Synchronize transactions from your PayPal Sandbox account to automatically detect recurring commitments and usage patterns.'
                          : 'Try broadening your search query or selecting "All" across filter categories.'}
                      </div>
                    </td>
                  </tr>
                ) : (
                  filtered.map((sub) => {
                    const name = sub.vendor_name || sub.name || 'Subscription';
                    const merchant = sub.merchant || sub.vendor_name || 'PayPal Merchant';
                    const amt = Number(sub.latest_amount || sub.amount || 0);
                    const priceCreep = Number(sub.price_change_pct || sub.priceCreepPct || 0);
                    const nextDate = sub.next_billing_date || sub.nextPaymentDate;
                    const tier = sub.tier || 'Tier 2 (Important)';
                    const isEssential = tier.includes('Tier 1');
                    const status = (sub.status || 'active').charAt(0).toUpperCase() + (sub.status || 'active').slice(1);
                    const cadence = (sub.cadence || 'monthly').toLowerCase();
                    const mEq = cadence === 'annual' ? amt / 12.0 : (cadence === 'quarterly' ? amt / 3.0 : (cadence === 'weekly' ? amt * 4.333 : amt));

                    return (
                      <tr key={sub.id || name}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                            <span style={{ fontWeight: 600, color: 'var(--navy-slate)', fontSize: '0.9rem' }}>{name}</span>
                            {sub.detection_type === 'potential' && (
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a' }}>
                                Potential
                              </span>
                            )}
                            {sub.billing_type === 'variable' && (
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                                Variable
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-caption)' }}>{merchant}</div>
                          {sub.detection_reason && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic', maxWidth: '320px', lineHeight: 1.3 }}>
                              {sub.detection_reason}
                            </div>
                          )}
                          {priceCreep > 0 && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--rose-dark)', fontWeight: 600, marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <TrendingUp size={11} /> +{priceCreep}% price creep
                            </div>
                          )}
                        </td>
                        <td style={{ fontSize: '0.84rem', color: 'var(--text-body)' }}>{sub.category || 'General Software'}</td>
                        <td>
                          <div style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>${amt.toFixed(2)}</div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-caption)', textTransform: 'capitalize' }}>{cadence}</div>
                        </td>
                        <td>
                          <div style={{ fontWeight: 700, color: 'var(--navy-primary)' }}>${mEq.toFixed(2)}/mo</div>
                        </td>
                        <td style={{ fontSize: '0.84rem', color: 'var(--text-body)', whiteSpace: 'nowrap' }}>
                          {nextDate ? new Date(nextDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Pending'}
                        </td>
                        <td><TierBadge tier={tier} /></td>
                        <td>
                          <span style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '0.25rem 0.55rem',
                            borderRadius: '4px',
                            background: isEssential ? 'var(--emerald-bg)' : 'var(--bg-subtle)',
                            color: isEssential ? 'var(--emerald-dark)' : 'var(--text-muted)',
                            border: `1px solid ${isEssential ? 'var(--emerald-border)' : 'var(--border-light)'}`,
                          }}>
                            {isEssential ? '✓ Essential' : 'Non-Essential'}
                          </span>
                        </td>
                        <td><StatusBadge status={status} /></td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
};

export default SubscriptionsPage;
