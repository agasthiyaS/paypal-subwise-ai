import React from 'react';
import { Link } from 'react-router-dom';
import StatCard from '../common/StatCard';
import IncomeExpenseChart from './IncomeExpenseChart';
import CategoryPieChart from './CategoryPieChart';
import {
  TrendingDown,
  DollarSign,
  CreditCard,
  Wallet,
  Calendar,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  ShoppingCart,
  Zap,
  Home,
  Users,
  Settings,
  RefreshCw,
} from 'lucide-react';

const HouseholdDashboardView = ({
  business,
  filteredTransactions,
  hasTransactions,
  loadingData,
  essentialReady = true,
  importantReady = true,
  advancedReady = true,
  syncing,
  syncStatus,
  handleSync,
  handleToggleMode,
  handleResetDemo,
  setModalOpen,
  setTestPaymentModalOpen,
  isDemo,
  isSandbox,
  isLive,
  formatLastSync,
  displayCompanyName,
  operatingCount,
  monthlyIncome,
  monthlyExpenses,
  fundingInflows,
  totalSubSpend,
  activeSubsCount,
  verifiedCashBalance,
  runwayStatus,
  healthData,
  potentialSavings,
  potentialAnnualSavings,
  recommendations,
  upcomingPayments,
  upcomingTotal,
  subAnalysis,
  monthlyChartData,
  categoryPieData,
  expenseSummary,
  unifiedIntelligence,
}) => {
  // Household-specific metric derivations from actual records
  const actualGroceries = expenseSummary?.grocery_total ?? 0;
  const actualUtilities = expenseSummary?.utility_total ?? 0;
  const householdBudget =
    expenseSummary && expenseSummary.overall_budget > 0
      ? expenseSummary.overall_budget
      : business?.monthly_baseline_revenue || 0;
  const hasBudget = householdBudget > 0;
  const budgetVariance = hasBudget ? householdBudget - monthlyExpenses : 0;
  const isUnderBudget = hasBudget ? budgetVariance >= 0 : true;

  // Grounded recommendations
  const householdRecs =
    Array.isArray(recommendations) && recommendations.length > 0 ? recommendations.slice(0, 3) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', background: '#eff6ff', color: 'var(--paypal-blue)', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.35rem' }}>
            <Home size={12} /> Household Intelligence
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--navy-slate)', letterSpacing: '-0.02em', marginBottom: '0.15rem' }}>
            Household Intelligence
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            {displayCompanyName} — Master groceries, monitor utility bills, and pool family streaming services
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Link
            to="/household"
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem', minHeight: '36px', padding: '0.45rem 0.95rem' }}
          >
            <Users size={15} color="var(--paypal-blue)" />
            <span>Household Hub</span>
          </Link>
          <button
            onClick={() => setModalOpen(true)}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem', minHeight: '36px', padding: '0.45rem 0.95rem' }}
          >
            <Settings size={15} color="var(--paypal-blue)" />
            <span>PayPal Setup</span>
          </button>
          <Link
            to="/recommendations"
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', minHeight: '36px', padding: '0.45rem 1rem', fontSize: '0.85rem' }}
          >
            <span>Family Savings Directives</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Sync Shared Stream Banner */}
      <div className="fintech-card" style={{
        padding: '0.95rem 1.25rem',
        background: isDemo ? '#faf5ff' : '#eff6ff',
        border: `1px solid ${isDemo ? '#ddd6fe' : '#bfdbfe'}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: isDemo ? '#ede9fe' : '#dbeafe',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDemo ? '#7c3aed' : 'var(--paypal-blue)',
              flexShrink: 0
            }}>
              {isDemo ? <Sparkles size={18} /> : <Home size={18} />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Household Pool' : 'Shared Household PayPal Feed'}
                </span>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.55rem',
                  borderRadius: '9999px',
                  background: isDemo ? '#ede9fe' : '#dcfce7',
                  color: isDemo ? '#6d28d9' : '#15803d',
                  border: `1px solid ${isDemo ? '#c4b5fd' : '#86efac'}`
                }}>
                  {isDemo ? 'Simulation' : 'Connected'}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {filteredTransactions.length} shared records ({operatingCount} active transactions) · Last updated {formatLastSync(business?.last_synced_at)}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {isDemo ? (
              <>
                <button
                  onClick={handleResetDemo}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ minHeight: '34px', fontSize: '0.82rem', background: '#6d28d9', borderColor: '#5b21b6' }}
                >
                  <RefreshCw size={13} className={syncing ? 'spin' : ''} />
                  <span>{syncing ? 'Resetting...' : 'Reset Demo'}</span>
                </button>
                <button
                  onClick={() => handleToggleMode('sandbox')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ minHeight: '34px', fontSize: '0.82rem' }}
                >
                  <span>To Sandbox</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ minHeight: '34px', fontSize: '0.82rem' }}
                >
                  <RefreshCw size={13} className={syncing ? 'spin' : ''} />
                  <span>{syncing ? 'Syncing...' : 'Sync Shared Feed'}</span>
                </button>
                {isSandbox && (
                  <button
                    onClick={() => setTestPaymentModalOpen(true)}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    style={{ minHeight: '34px', fontSize: '0.82rem', borderColor: '#fde68a', color: '#92400e', background: '#fffbeb', fontWeight: 600 }}
                  >
                    <CreditCard size={13} />
                    <span>Test Checkout ($5)</span>
                  </button>
                )}
                <button
                  onClick={() => handleToggleMode('demo')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ minHeight: '34px', fontSize: '0.82rem', background: '#faf5ff', color: '#7c3aed', borderColor: '#ddd6fe', fontWeight: 600 }}
                >
                  <Sparkles size={13} />
                  <span>Demo Mode</span>
                </button>
              </>
            )}
          </div>
        </div>

        {syncStatus && (
          <div style={{
            marginTop: '0.65rem',
            padding: '0.55rem 0.85rem',
            borderRadius: '6px',
            fontSize: '0.82rem',
            fontWeight: 600,
            background: syncStatus.type === 'error' ? '#fee2e2' : '#f0fdf4',
            color: syncStatus.type === 'error' ? '#b91c1c' : '#15803d',
            border: `1px solid ${syncStatus.type === 'error' ? '#fca5a5' : '#86efac'}`
          }}>
            {syncStatus.text}
          </div>
        )}
      </div>

      {/* KPI Cards — Household Perspective with Hero Card */}
      <div className="stat-grid">
        <StatCard
          title="Shared Cash Pool"
          value={verifiedCashBalance !== null ? `$${verifiedCashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Not available"}
          subtext="Liquid funds available for household expenses"
          icon={Wallet}
          isPositiveGood={true}
          hero={true}
        />
        <StatCard
          title="Monthly Shared Outflow"
          value={`$${monthlyExpenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={
            hasBudget
              ? isUnderBudget
                ? `$${budgetVariance.toFixed(0)} under monthly budget`
                : `$${Math.abs(budgetVariance).toFixed(0)} over budget`
              : "No monthly budget set"
          }
          icon={TrendingDown}
          isPositiveGood={hasBudget ? isUnderBudget : true}
        />
        <StatCard
          title="Groceries &amp; Staples"
          value={actualGroceries > 0 ? `$${actualGroceries.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "$0.00"}
          subtext={actualGroceries > 0 ? "Supermarkets, food & pantry records" : "No grocery expenses recorded"}
          icon={ShoppingCart}
          isPositiveGood={false}
        />
        <StatCard
          title="Utilities &amp; Telecom"
          value={actualUtilities > 0 ? `$${actualUtilities.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "$0.00"}
          subtext={actualUtilities > 0 ? "Electricity, water, gas & internet" : "No utility expenses recorded"}
          icon={Zap}
          isPositiveGood={false}
        />
      </div>

      {/* Household Budget & Smart Benchmarks Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {/* Budget Status Card */}
        <div className="fintech-card" style={{ padding: '1.25rem', border: `1px solid ${!hasBudget ? 'var(--border-light)' : isUnderBudget ? '#bbf7d0' : '#fca5a5'}`, background: !hasBudget ? 'var(--bg-surface)' : isUnderBudget ? '#f0fdf4' : '#fff1f2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: !hasBudget ? 'var(--text-muted)' : isUnderBudget ? '#15803d' : '#b91c1c', marginBottom: '0.35rem' }}>
                Household Budget Status
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: !hasBudget ? 'var(--navy-slate)' : isUnderBudget ? '#15803d' : '#b91c1c', lineHeight: 1.1 }}>
                {!hasBudget ? 'No Budget Set' : isUnderBudget ? 'On Target' : 'Over Budget'}
              </div>
              <p style={{ fontSize: '0.8rem', color: !hasBudget ? 'var(--text-muted)' : isUnderBudget ? '#166534' : '#991b1b', marginTop: '0.4rem', lineHeight: 1.45 }}>
                {!hasBudget
                  ? 'Set a monthly household budget in the workspace to monitor shared limits.'
                  : isUnderBudget
                  ? `You have a $${budgetVariance.toFixed(2)} safety cushion remaining for this month.`
                  : `Shared outflows exceed target budget by $${Math.abs(budgetVariance).toFixed(2)}.`}
              </p>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: !hasBudget ? 'var(--bg-subtle)' : isUnderBudget ? '#bbf7d0' : '#fecaca', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Home size={20} color={!hasBudget ? 'var(--text-muted)' : isUnderBudget ? '#15803d' : '#b91c1c'} />
            </div>
          </div>
        </div>

        {/* Household Savings Intelligence Card */}
        <div className="fintech-card" style={{ padding: '1.25rem', border: '1px solid #bfdbfe', background: '#eff6ff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--paypal-blue)', marginBottom: '0.35rem' }}>
                Household Savings Intelligence
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--navy-primary)', lineHeight: 1.1 }}>
                {potentialSavings > 0 ? `Save $${potentialSavings.toFixed(2)}/mo` : '$0.00/mo'}
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--navy-slate)', marginTop: '0.4rem', lineHeight: 1.45 }}>
                {potentialSavings > 0
                  ? `Identified optimizations across shared subscriptions and recurring services.`
                  : `No recurring household overhead redundancies detected. SubWise monitors continuously.`}
              </p>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShoppingCart size={20} color="var(--paypal-blue)" />
            </div>
          </div>
        </div>
      </div>

      {/* Household Directives */}
      <div className="fintech-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
              Household Savings Directives
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
              Actionable recommendations to minimize shared household overhead
            </p>
          </div>
          <Link to="/recommendations" style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            View All Directives <ArrowRight size={13} />
          </Link>
        </div>

        {!advancedReady ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
            {[1, 2, 3].map(i => (
              <div key={i} style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '1rem', height: '110px' }}>
                <div style={{ width: '35%', height: '14px', background: '#e2e8f0', borderRadius: '4px', marginBottom: '0.65rem', animation: 'pulse 1.5s infinite' }} />
                <div style={{ width: '70%', height: '16px', background: '#cbd5e1', borderRadius: '4px', marginBottom: '0.5rem', animation: 'pulse 1.5s infinite' }} />
                <div style={{ width: '90%', height: '12px', background: '#f1f5f9', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
              </div>
            ))}
          </div>
        ) : householdRecs.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
            {householdRecs.map((rec, idx) => (
              <div key={rec.id || idx} style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '0.95rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.12rem 0.45rem', borderRadius: '4px', background: rec.potential_monthly_savings > 0 ? '#ecfdf5' : 'var(--bg-subtle)', color: rec.potential_monthly_savings > 0 ? '#059669' : 'var(--text-muted)' }}>
                    {rec.potential_monthly_savings > 0 ? `Save $${rec.potential_monthly_savings.toFixed(2)}/mo` : (rec.action_type || 'Optimization')}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>{rec.category || rec.service_name || 'Household'}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
                  {rec.title || rec.service_name || 'Savings Opportunity'}
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-body)', lineHeight: 1.45, margin: 0 }}>
                  {rec.description || rec.reasoning || 'Actionable intelligence to reduce shared spending.'}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: '8px', border: '1px dashed var(--border-medium)' }}>
            <CheckCircle2 size={32} color="#10b981" style={{ margin: '0 auto 0.5rem auto' }} />
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
              No Active Household Directives
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', maxWidth: '420px', margin: '0 auto 1rem auto', lineHeight: 1.5 }}>
              All household spending and shared subscriptions are optimized. As household members log shared expenses, SubWise AI will identify consolidation opportunities.
            </p>
            <Link to="/expenses" className="btn-fintech btn-fintech-outline btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.82rem' }}>
              Log New Expense <ArrowRight size={13} />
            </Link>
          </div>
        )}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1rem' }}>
        {!importantReady ? (
          <>
            <div className="fintech-card" style={{ height: '320px', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
              Loading household spending trends...
            </div>
            <div className="fintech-card" style={{ height: '320px', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
              Loading shared categories...
            </div>
          </>
        ) : (
          <>
            <IncomeExpenseChart data={monthlyChartData} />
            <CategoryPieChart data={categoryPieData} />
          </>
        )}
      </div>

      {/* Upcoming Household Bills */}
      <div className="fintech-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
              Upcoming Shared Household Bills
            </h3>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Total scheduled renewals: ${upcomingTotal.toFixed(2)}
            </div>
          </div>
          <Calendar size={18} color="var(--paypal-blue)" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {upcomingPayments.length > 0 ? (
            upcomingPayments.map((p) => (
              <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.45rem 0', borderBottom: '1px solid var(--border-light)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--navy-slate)' }}>{p.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Due: {p.date}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span style={{ fontWeight: 750, fontSize: '0.9rem', color: 'var(--navy-slate)' }}>${Number(p.amount).toFixed(2)}</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.12rem 0.45rem', background: '#f0fdf4', color: '#166534', borderRadius: '4px', fontWeight: 600 }}>Scheduled</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '1.25rem 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              No upcoming shared household bills detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HouseholdDashboardView;
