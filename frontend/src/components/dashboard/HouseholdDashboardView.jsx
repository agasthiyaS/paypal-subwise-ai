import React from 'react';
import { Link } from 'react-router-dom';
import StatCard from '../common/StatCard';
import IncomeExpenseChart from './IncomeExpenseChart';
import CategoryPieChart from './CategoryPieChart';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  Wallet,
  Activity,
  Calendar,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  ShoppingCart,
  Zap,
  Home,
  Users,
  Percent,
  Settings
} from 'lucide-react';

const HouseholdDashboardView = ({
  business,
  filteredTransactions,
  hasTransactions,
  loadingData,
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
}) => {
  // Household-specific metric derivations
  const estimatedGroceries = Math.round(monthlyExpenses * 0.38 * 100) / 100;
  const estimatedUtilities = Math.round(monthlyExpenses * 0.22 * 100) / 100;
  const householdBudget = business?.monthly_baseline_revenue || 3500;
  const budgetVariance = householdBudget - monthlyExpenses;
  const isUnderBudget = budgetVariance >= 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', background: '#eff6ff', color: '#0070ba', padding: '0.3rem 0.8rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            <Home size={14} /> Household Budget &amp; Shared Expenses
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.35rem', lineHeight: 1.25 }}>
            Household Intelligence
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            {displayCompanyName} — Master groceries, monitor utility bills, and pool family streaming services
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => setModalOpen(true)}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', fontSize: '0.92rem', minHeight: '44px', padding: '0.5rem 1.15rem' }}
          >
            <Settings size={16} color="var(--paypal-blue)" />
            <span>PayPal Setup</span>
          </button>
          <Link
            to="/recommendations"
            className="btn-fintech btn-fintech-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', minHeight: '44px', padding: '0.5rem 1.25rem', fontSize: '0.92rem' }}
          >
            <span>Household Savings Advice</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      {/* Sync Stream Banner */}
      <div className="fintech-card" style={{
        padding: '1.5rem 2rem',
        background: isDemo
          ? 'linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%)'
          : 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%)',
        border: `1.5px solid ${isDemo ? '#c4b5fd' : '#bbf7d0'}`,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '12px',
              background: isDemo ? '#ede9fe' : '#dcfce7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDemo ? '#7c3aed' : '#15803d',
              fontWeight: 800,
              fontSize: '1.25rem'
            }}>
              {isDemo ? <Sparkles size={24} /> : <Home size={24} />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Household Workspace' : 'Household PayPal Stream'}
                </span>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.6rem',
                  borderRadius: '9999px',
                  background: isDemo ? '#ede9fe' : '#dcfce7',
                  color: isDemo ? '#6d28d9' : '#15803d',
                  border: `1px solid ${isDemo ? '#c4b5fd' : '#86efac'}`
                }}>
                  {isDemo ? 'Simulated Family Plan' : 'Connected'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {filteredTransactions.length} shared records ({operatingCount} active payments) · Last sync {formatLastSync(business?.last_synced_at)}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {isDemo ? (
              <>
                <button
                  onClick={handleResetDemo}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ minHeight: '42px', background: '#6d28d9', borderColor: '#5b21b6' }}
                >
                  <RefreshCw size={15} className={syncing ? 'spin-icon' : ''} />
                  <span>{syncing ? 'Resetting...' : 'Reset Demo'}</span>
                </button>
                <button
                  onClick={() => handleToggleMode('sandbox')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ minHeight: '42px' }}
                >
                  <span>Switch to Sandbox</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ minHeight: '42px', minWidth: '150px' }}
                >
                  <RefreshCw size={15} className={syncing ? 'spin-icon' : ''} />
                  <span>{syncing ? 'Syncing...' : 'Sync Shared Feed'}</span>
                </button>
                {isSandbox && (
                  <button
                    onClick={() => setTestPaymentModalOpen(true)}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    style={{ minHeight: '42px', borderColor: '#f59e0b', color: '#b45309', background: '#fffbeb', fontWeight: 700 }}
                  >
                    <CreditCard size={16} />
                    <span>Test Sandbox Checkout ($5)</span>
                  </button>
                )}
                <button
                  onClick={() => handleToggleMode('demo')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ minHeight: '42px', background: '#ede9fe', color: '#6d28d9', borderColor: '#c4b5fd', fontWeight: 700 }}
                >
                  <Sparkles size={16} />
                  <span>Load Demo Household</span>
                </button>
              </>
            )}
          </div>
        </div>

        {syncStatus && (
          <div style={{
            marginTop: '1rem',
            padding: '0.65rem 1rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            background: syncStatus.type === 'error' ? '#fee2e2' : '#f0fdf4',
            color: syncStatus.type === 'error' ? '#b91c1c' : '#15803d',
            border: `1px solid ${syncStatus.type === 'error' ? '#fca5a5' : '#86efac'}`
          }}>
            {syncStatus.text}
          </div>
        )}
      </div>

      {/* KPI Cards — Household Perspective */}
      <div className="stat-grid">
        <StatCard
          title="Shared Cash Pool"
          value={verifiedCashBalance !== null ? `$${verifiedCashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Not available"}
          subtext="Liquid funds available for household expenses"
          icon={Wallet}
          isPositiveGood={true}
        />
        <StatCard
          title="Monthly Shared Outflow"
          value={`$${monthlyExpenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={isUnderBudget ? `$${budgetVariance.toFixed(0)} under monthly budget` : `$${Math.abs(budgetVariance).toFixed(0)} over budget`}
          icon={TrendingDown}
          isPositiveGood={isUnderBudget}
        />
        <StatCard
          title="Groceries &amp; Staples"
          value={`$${estimatedGroceries.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext="Supermarkets, wholesale clubs &amp; pantries"
          icon={ShoppingCart}
          isPositiveGood={false}
        />
        <StatCard
          title="Utilities &amp; Telecom"
          value={`$${estimatedUtilities.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext="Electricity, water, gas &amp; broadband"
          icon={Zap}
          isPositiveGood={false}
        />
      </div>

      {/* Household Budget & Smart Benchmarks Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Budget Status Card */}
        <div className="fintech-card" style={{ padding: '1.75rem', border: `1.5px solid ${isUnderBudget ? '#a7f3d0' : '#fca5a5'}`, background: isUnderBudget ? '#f0fdf4' : '#fff1f2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: isUnderBudget ? '#15803d' : '#b91c1c', marginBottom: '0.4rem' }}>
                Household Budget Status
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: isUnderBudget ? '#15803d' : '#b91c1c', lineHeight: 1.1 }}>
                {isUnderBudget ? 'On Target' : 'Over Budget'}
              </div>
              <p style={{ fontSize: '0.85rem', color: isUnderBudget ? '#166534' : '#991b1b', marginTop: '0.5rem', lineHeight: 1.45 }}>
                {isUnderBudget
                  ? `You have a $${budgetVariance.toFixed(2)} safety cushion remaining for this month's shared pool.`
                  : `Shared outflows exceed your target budget by $${Math.abs(budgetVariance).toFixed(2)}. Consider trimming non-essential subscriptions.`}
              </p>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: isUnderBudget ? '#bbf7d0' : '#fecaca', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Home size={24} color={isUnderBudget ? '#15803d' : '#b91c1c'} />
            </div>
          </div>
        </div>

        {/* Grocery & Vendor Benchmarking Insight */}
        <div className="fintech-card" style={{ padding: '1.75rem', border: '1.5px solid #bfdbfe', background: '#eff6ff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#0070ba', marginBottom: '0.4rem' }}>
                Supermarket Price Benchmark
              </div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#003087', lineHeight: 1.1 }}>
                Save ~$140/mo
              </div>
              <p style={{ fontSize: '0.85rem', color: '#1e3a8a', marginTop: '0.5rem', lineHeight: 1.45 }}>
                Comparing recent grocery items: Purchasing paper goods &amp; pantry staples at wholesale clubs saves an average 16% over local grocery retailers.
              </p>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShoppingCart size={24} color="#0070ba" />
            </div>
          </div>
        </div>
      </div>

      {/* Household Directives */}
      <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              Household Savings Directives
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Actionable recommendations to minimize shared household overhead
            </p>
          </div>
          <Link to="/recommendations" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            View All Directives <ArrowRight size={14} />
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.15rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: '#ecfdf5', color: '#059669' }}>
                Save $16/mo
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Streaming</span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a', marginBottom: '0.35rem' }}>
              Consolidate to Family Streaming Plan
            </div>
            <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45, margin: 0 }}>
              Multiple individual media subscriptions found. Switching to one family plan covers up to 6 members.
            </p>
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.15rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: '#fef3c7', color: '#d97706' }}>
                Inspect Anomaly
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Utilities</span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a', marginBottom: '0.35rem' }}>
              Electricity Peak Surge Check
            </div>
            <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45, margin: 0 }}>
              Recent power payments reflect a 22% increase over prior month. Check smart thermostat schedules.
            </p>
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.15rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: '#ecfdf5', color: '#059669' }}>
                Save $25/mo
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Telecom</span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a', marginBottom: '0.35rem' }}>
              Broadband Speed vs Pricing Check
            </div>
            <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45, margin: 0 }}>
              Your current fiber plan rate increased past promotional period. Renegotiate or apply retention credits.
            </p>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.25rem' }}>
        <IncomeExpenseChart data={monthlyChartData} />
        <CategoryPieChart data={categoryPieData} />
      </div>

      {/* Upcoming Household Bills */}
      <div className="fintech-card" style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              Upcoming Shared Household Bills
            </h3>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Total scheduled renewals: ${upcomingTotal.toFixed(2)}
            </div>
          </div>
          <Calendar size={20} color="var(--paypal-blue)" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {upcomingPayments.length > 0 ? (
            upcomingPayments.map((p) => (
              <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 0', borderBottom: '1px solid #f1f5f9' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>{p.name}</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Due: {p.date}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>${Number(p.amount).toFixed(2)}</span>
                  <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', background: '#f0fdf4', color: '#166534', borderRadius: '4px', fontWeight: 600 }}>Scheduled</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '1.5rem 0', color: '#64748b', fontSize: '0.88rem' }}>
              No upcoming shared household bills detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HouseholdDashboardView;
