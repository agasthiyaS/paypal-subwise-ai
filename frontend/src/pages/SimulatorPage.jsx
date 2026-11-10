import React, { useState, useEffect, useMemo } from 'react';
import { subscriptionsAPI, forecastAPI, paypalAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend
} from 'recharts';
import { Play, RotateCcw, TrendingDown, TrendingUp, Wallet, Calendar, Zap, Info, RefreshCw } from 'lucide-react';

const fmt = (n) => `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * SimulatorPage — interactive what-if cash-flow scenario simulator.
 * All calculations are deterministic and performed in the browser.
 * Uses real subscription and business profile data from the backend.
 */
const SimulatorPage = () => {
  const { business, refreshBusiness } = useAuth();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);
  const [forecastBaseline, setForecastBaseline] = useState(null);

  /* ---- Simulator inputs ---- */
  const [newSubCost, setNewSubCost] = useState(0);
  const [revenueShockPct, setRevenueShockPct] = useState(0);
  const [expenseChangePct, setExpenseChangePct] = useState(0);
  const [durationMonths, setDurationMonths] = useState(6);
  const [freezeTier3, setFreezeTier3] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [subRes, forecastRes] = await Promise.allSettled([
        subscriptionsAPI.getSubscriptions(),
        forecastAPI.getForecast(6),
      ]);
      if (subRes.status === 'fulfilled' && subRes.value?.subscriptions) {
        setSubscriptions(subRes.value.subscriptions || []);
      }
      if (forecastRes.status === 'fulfilled') {
        setForecastBaseline(forecastRes.value);
      }
    } catch (err) {
      console.error('Failed to load simulator data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [business?.id]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await paypalAPI.sync();
      setSyncStatus({ type: 'success', text: res.message || 'Sync complete.' });
      await refreshBusiness();
      await loadData();
    } catch (err) {
      setSyncStatus({ type: 'error', text: err.response?.data?.detail || 'Sync failed.' });
    } finally {
      setSyncing(false);
    }
  };

  // Derive baseline metrics from the centralized backend forecast engine.
  // Falls back to zero — never uses hardcoded $15,000 revenue or $45,000 cash defaults.
  const baseline = useMemo(() => {
    const verifiedBalance = forecastBaseline?.verified_starting_cash ?? 0.0;
    const totalIncome = forecastBaseline?.historical_monthly_operating_revenue ?? 0.0;
    // Total expenses = historical non-sub + confirmed subscription commitments
    const confirmedSubCommit = forecastBaseline?.confirmed_monthly_subscription_commitments ?? 0.0;
    const nonSubExpenses = forecastBaseline?.historical_monthly_non_sub_expenses ?? 0.0;
    const totalExpenses = nonSubExpenses + confirmedSubCommit;
    const subSpend = subscriptions.reduce((s, sub) => s + Number(sub.latest_amount || 0), 0);
    return {
      totalIncome,
      totalExpenses: Math.max(totalExpenses, confirmedSubCommit),
      subscriptionExpenses: subSpend,
      availableCashBalance: verifiedBalance,
      forecastStatus: forecastBaseline?.status ?? 'insufficient_data',
    };
  }, [forecastBaseline, subscriptions]);

  const hasData = subscriptions.length > 0 || baseline.totalIncome > 0 || baseline.availableCashBalance > 0;

  const tier3Subs = useMemo(() =>
    subscriptions.filter((s) => (s.tier || '').includes('Tier 3')),
    [subscriptions]
  );
  const tier3Total = tier3Subs.reduce((acc, s) => acc + Number(s.latest_amount || 0), 0);
  const tier3Names = tier3Subs.map(s => s.vendor_name || 'Tool').slice(0, 4).join(', ');

  /* ---- Derived simulation ---- */
  const simulation = useMemo(() => {
    if (!hasRun) return null;

    const monthlyIncome = baseline.totalIncome * (1 + revenueShockPct / 100);
    const baseExpenses = baseline.totalExpenses * (1 + expenseChangePct / 100);
    const frozenSavings = freezeTier3 ? tier3Total : 0;
    const monthlyExpenses = baseExpenses + newSubCost - frozenSavings;
    const monthlyNet = monthlyIncome - monthlyExpenses;
    const startBalance = baseline.availableCashBalance;

    const timeline = [];
    let balance = startBalance;
    const today = new Date();

    for (let i = 0; i < durationMonths; i++) {
      balance += monthlyNet;
      const fDate = new Date(today.getFullYear(), today.getMonth() + i + 1, 1);
      const label = fDate.toLocaleString('en-US', { month: 'short', year: '2-digit' });
      timeline.push({
        month: label,
        simulatedBalance: Math.max(0, balance),
        baselineBalance: Math.max(0, startBalance + (i + 1) * (baseline.totalIncome - baseline.totalExpenses)),
        income: monthlyIncome,
        expenses: monthlyExpenses,
      });
    }

    const finalBalance = timeline[timeline.length - 1]?.simulatedBalance || 0;
    const baselineFinal = timeline[timeline.length - 1]?.baselineBalance || 0;
    const impactDelta = finalBalance - baselineFinal;
    const runwayMonths = monthlyNet >= 0
      ? 99
      : Math.max(0, Math.floor(startBalance / Math.abs(monthlyNet)));

    return { timeline, monthlyIncome, monthlyExpenses, monthlyNet, finalBalance, impactDelta, runwayMonths, tier3Total, frozenSavings };
  }, [hasRun, newSubCost, revenueShockPct, expenseChangePct, durationMonths, freezeTier3, baseline, tier3Total]);

  const handleRun = () => setHasRun(true);
  const handleReset = () => {
    setNewSubCost(0);
    setRevenueShockPct(0);
    setExpenseChangePct(0);
    setDurationMonths(6);
    setFreezeTier3(false);
    setHasRun(false);
  };

  const sliderStyle = { width: '100%', cursor: 'pointer', accentColor: 'var(--navy-primary)' };
  const getRevenueColor = () => revenueShockPct < -20 ? 'var(--rose-dark)' : revenueShockPct < 0 ? 'var(--amber-dark)' : 'var(--emerald-dark)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.45rem', lineHeight: 1.25 }}>
            Scenario Simulator
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
            Model what-if cash-flow scenarios: revenue shocks, new subscriptions, expense changes — deterministic calculations
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', minHeight: '44px' }}
          >
            <RefreshCw size={16} className={syncing ? 'spin-icon' : ''} />
            <span>Sync PayPal</span>
          </button>
        </div>
      </div>

      {syncStatus && (
        <div style={{
          padding: '0.95rem 1.35rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '1rem',
          background: syncStatus.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: syncStatus.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
          border: `1.5px solid ${syncStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`
        }}>
          {syncStatus.text}
        </div>
      )}

      {/* Disclaimer */}
      <div style={{
        display: 'flex', alignItems: 'flex-start', gap: '0.85rem',
        background: 'var(--indigo-bg)', border: '1.5px solid #c7d2fe',
        borderRadius: 'var(--radius-lg)', padding: '1.15rem 1.5rem',
        fontSize: '1rem', color: '#4338ca', lineHeight: 1.6,
      }}>
        <Info size={20} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
        <span>
          All scenario projections are computed deterministically from your{' '}
          <strong>{baseline.forecastStatus !== 'insufficient_data' ? 'backend-verified' : 'unverified'}</strong> financial baseline
          {baseline.forecastStatus === 'insufficient_data' && ' — insufficient operating transaction history'}.
          Baseline: <strong>{fmt(baseline.totalIncome)}/mo revenue</strong> · <strong>{fmt(baseline.totalExpenses)}/mo expenses</strong> · <strong>{fmt(baseline.availableCashBalance)} starting cash</strong>.
          Source: Forecast Engine (verified PayPal ledger). No AI models are used to generate numbers.
        </span>
      </div>

      {!hasData && !loading && (
        <div className="fintech-card" style={{
          padding: '2rem',
          textAlign: 'center',
          background: 'var(--bg-subtle)',
          border: '1.5px dashed var(--border-medium)',
        }}>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', margin: '0 auto 1rem', maxWidth: '500px' }}>
            Synchronize PayPal transactions to populate your financial baseline for simulation.
            Use the <strong>Sync PayPal</strong> button above to fetch real transaction data.
          </p>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-fintech btn-fintech-primary"
            style={{ minHeight: '46px', padding: '0.65rem 1.5rem' }}
          >
            Sync PayPal Sandbox
          </button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 460px) 1fr', gap: '2rem', alignItems: 'start' }}>

        {/* Controls Panel */}
        <div className="fintech-card" style={{ padding: '2.25rem' }}>
          <h3 style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1.75rem' }}>
            Scenario Parameters
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.65rem' }}>

            {/* New Subscription Cost */}
            <div>
              <label className="form-label" style={{ fontSize: '1.05rem', marginBottom: '0.65rem' }}>
                New Subscription Cost (USD/month)
                <span style={{ float: 'right', fontWeight: 800, color: 'var(--navy-primary)', fontFamily: 'JetBrains Mono, monospace' }}>{fmt(newSubCost)}</span>
              </label>
              <input
                type="range"
                min={0}
                max={1000}
                step={10}
                value={newSubCost}
                onChange={(e) => setNewSubCost(Number(e.target.value))}
                style={sliderStyle}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.45rem' }}>
                <span>$0</span><span>$1,000/mo</span>
              </div>
            </div>

            {/* Revenue Shock */}
            <div>
              <label className="form-label">
                Revenue Change (%)
                <span style={{ float: 'right', fontWeight: 700, color: getRevenueColor() }}>
                  {revenueShockPct > 0 ? '+' : ''}{revenueShockPct}%
                </span>
              </label>
              <input
                type="range"
                min={-60}
                max={50}
                step={5}
                value={revenueShockPct}
                onChange={(e) => setRevenueShockPct(Number(e.target.value))}
                style={sliderStyle}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-caption)', marginTop: '0.3rem' }}>
                <span>-60% (Severe Shock)</span><span>+50% (Growth)</span>
              </div>
            </div>

            {/* Expense Change */}
            <div>
              <label className="form-label">
                Expense Change (%)
                <span style={{ float: 'right', fontWeight: 700, color: expenseChangePct > 0 ? 'var(--rose-dark)' : 'var(--emerald-dark)' }}>
                  {expenseChangePct > 0 ? '+' : ''}{expenseChangePct}%
                </span>
              </label>
              <input
                type="range"
                min={-30}
                max={50}
                step={5}
                value={expenseChangePct}
                onChange={(e) => setExpenseChangePct(Number(e.target.value))}
                style={sliderStyle}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-caption)', marginTop: '0.3rem' }}>
                <span>-30% (Cost Cuts)</span><span>+50% (Overspend)</span>
              </div>
            </div>

            {/* Duration */}
            <div>
              <label className="form-label">
                Simulation Duration
                <span style={{ float: 'right', fontWeight: 700, color: 'var(--navy-primary)' }}>{durationMonths} months</span>
              </label>
              <input
                type="range"
                min={1}
                max={12}
                step={1}
                value={durationMonths}
                onChange={(e) => setDurationMonths(Number(e.target.value))}
                style={sliderStyle}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-caption)', marginTop: '0.3rem' }}>
                <span>1 month</span><span>12 months</span>
              </div>
            </div>

            {/* Freeze Tier 3 toggle */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              background: freezeTier3 ? 'var(--emerald-bg)' : 'var(--bg-subtle)',
              border: `1px solid ${freezeTier3 ? 'var(--emerald-border)' : 'var(--border-light)'}`,
              borderRadius: 'var(--radius-md)',
              padding: '0.85rem 1rem',
              cursor: 'pointer',
            }} onClick={() => setFreezeTier3(!freezeTier3)}>
              <input
                type="checkbox"
                checked={freezeTier3}
                onChange={() => setFreezeTier3(!freezeTier3)}
                style={{ marginTop: '0.1rem', cursor: 'pointer', accentColor: 'var(--emerald-dark)' }}
                onClick={e => e.stopPropagation()}
              />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--navy-slate)' }}>
                  Freeze All Tier 3 (Discretionary) Subscriptions
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  {tier3Total > 0
                    ? `Saves ${fmt(tier3Total)}/mo by pausing ${tier3Names || 'discretionary tools'}`
                    : 'No Tier 3 subscriptions detected — sync transactions first'}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleRun}
                style={{
                  flex: 2,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                  padding: '0.85rem',
                  background: 'var(--navy-primary)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  letterSpacing: '0.01em',
                  boxShadow: '0 2px 8px rgba(0,48,135,0.2)',
                }}
              >
                <Play size={16} />
                Run Simulation
              </button>
              <button
                onClick={handleReset}
                style={{
                  flex: 1,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
                  padding: '0.85rem',
                  background: 'var(--bg-subtle)',
                  color: 'var(--text-body)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={14} />
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {!hasRun ? (
            <div className="fintech-card" style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              border: '2px dashed var(--border-medium)',
              background: 'var(--bg-subtle)',
            }}>
              <Zap size={36} color="var(--text-caption)" style={{ margin: '0 auto 1rem' }} />
              <div style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: '1rem', marginBottom: '0.5rem' }}>
                Configure Parameters and Run Simulation
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-caption)', maxWidth: '320px', margin: '0 auto' }}>
                Adjust the sliders on the left to model a revenue shock, new subscription, or expense change, then click "Run Simulation".
              </p>
            </div>
          ) : simulation && (
            <>
              {/* Result KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '1rem' }}>
                {[
                  {
                    label: 'Simulated Monthly Income',
                    value: fmt(simulation.monthlyIncome),
                    icon: TrendingUp,
                    color: 'var(--emerald-dark)',
                    bg: 'var(--emerald-bg)',
                    border: 'var(--emerald-border)',
                  },
                  {
                    label: 'Simulated Monthly Expenses',
                    value: fmt(simulation.monthlyExpenses),
                    icon: TrendingDown,
                    color: 'var(--rose-dark)',
                    bg: 'var(--rose-bg)',
                    border: 'var(--rose-border)',
                  },
                  {
                    label: `Balance After ${durationMonths} Months`,
                    value: fmt(simulation.finalBalance),
                    icon: Wallet,
                    color: simulation.finalBalance > baseline.availableCashBalance ? 'var(--emerald-dark)' : 'var(--rose-dark)',
                    bg: simulation.finalBalance > baseline.availableCashBalance ? 'var(--emerald-bg)' : 'var(--rose-bg)',
                    border: simulation.finalBalance > baseline.availableCashBalance ? 'var(--emerald-border)' : 'var(--rose-border)',
                  },
                  {
                    label: 'Estimated Runway',
                    value: simulation.runwayMonths >= 99 ? 'Sustainable' : `${simulation.runwayMonths} months`,
                    icon: Calendar,
                    color: simulation.runwayMonths >= 6 ? 'var(--emerald-dark)' : 'var(--rose-dark)',
                    bg: simulation.runwayMonths >= 6 ? 'var(--emerald-bg)' : 'var(--rose-bg)',
                    border: simulation.runwayMonths >= 6 ? 'var(--emerald-border)' : 'var(--rose-border)',
                  },
                ].map((kpi) => (
                  <div key={kpi.label} className="fintech-card" style={{
                    padding: '1rem 1.1rem',
                    border: `1px solid ${kpi.border}`,
                    background: kpi.bg,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: kpi.color, marginBottom: '0.4rem' }}>
                          {kpi.label}
                        </div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy-slate)', lineHeight: 1 }}>
                          {kpi.value}
                        </div>
                      </div>
                      <kpi.icon size={18} color={kpi.color} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Impact Delta Alert */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-md)',
                background: simulation.impactDelta >= 0 ? 'var(--emerald-bg)' : 'var(--rose-bg)',
                border: `1px solid ${simulation.impactDelta >= 0 ? 'var(--emerald-border)' : 'var(--rose-border)'}`,
                fontSize: '0.9rem',
              }}>
                {simulation.impactDelta >= 0
                  ? <TrendingUp size={20} color="var(--emerald-dark)" />
                  : <TrendingDown size={20} color="var(--rose-dark)" />
                }
                <div>
                  <span style={{ fontWeight: 700, color: simulation.impactDelta >= 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)' }}>
                    Scenario Impact: {simulation.impactDelta >= 0 ? '+' : ''}{fmt(simulation.impactDelta)} vs baseline
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginLeft: '0.5rem' }}>
                    over {durationMonths} months
                  </span>
                </div>
                {simulation.frozenSavings > 0 && (
                  <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--emerald-dark)', fontWeight: 600 }}>
                    +{fmt(simulation.frozenSavings)}/mo Tier 3 saved
                  </span>
                )}
              </div>

              {/* Simulation Chart */}
              <div className="fintech-card" style={{ padding: '1.5rem' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
                  Projected Balance: Scenario vs Baseline
                </h3>
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={simulation.timeline} margin={{ top: 5, right: 15, left: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="simGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0070ba" stopOpacity={0.18} />
                        <stop offset="95%" stopColor="#0070ba" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="baseGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.1} />
                        <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} width={55} />
                    <Tooltip formatter={(v) => fmt(v)} />
                    <Legend wrapperStyle={{ fontSize: '0.82rem' }} />
                    <Area type="monotone" dataKey="simulatedBalance" name="Simulated Balance" stroke="#0070ba" strokeWidth={2.5} fill="url(#simGrad)" dot={false} />
                    <Area type="monotone" dataKey="baselineBalance" name="Baseline Balance" stroke="#94a3b8" strokeWidth={1.5} fill="url(#baseGrad)" strokeDasharray="5 3" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulatorPage;
