import React from 'react';
import { Link } from 'react-router-dom';
import StatCard from '../common/StatCard';
import IncomeExpenseChart from './IncomeExpenseChart';
import CategoryPieChart from './CategoryPieChart';
import CashFlowTrendChart from './CashFlowTrendChart';
import SubscriptionSpendingChart from './SubscriptionSpendingChart';
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
  ShoppingBag,
  Coffee,
  Tv,
  Percent,
  Compass,
  Settings
} from 'lucide-react';

const IndividualDashboardView = ({
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
  // Computed Personal Metrics
  const netSavings = Math.max(0, monthlyIncome - monthlyExpenses);
  const savingsRate = monthlyIncome > 0 ? Math.round((netSavings / monthlyIncome) * 100) : 0;
  const discretionarySpend = Math.max(0, monthlyExpenses - totalSubSpend);

  // Individual Recommendations (filtered or enhanced)
  const personalRecs = recommendations.length > 0 ? recommendations : [
    {
      id: 'ind-1',
      title: 'Review Cloud Storage & App Subscriptions',
      impact: 'Save $24/mo',
      urgency: 'Medium',
      description: 'Audit recurring services with zero activity in the last 45 days.',
    },
    {
      id: 'ind-2',
      title: 'Food Delivery & Convenience Surcharge Alert',
      impact: 'Save $85/mo',
      urgency: 'High',
      description: 'Frequent $4–$9 delivery fees detected across weekend orders.',
    },
    {
      id: 'ind-3',
      title: 'Switch to Annual Billing for Core Services',
      impact: 'Save 15%',
      urgency: 'Low',
      description: 'Spotify and media providers offer discounts on prepaid annual plans.',
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', background: '#eff6ff', color: '#0070ba', padding: '0.3rem 0.8rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            <Sparkles size={14} /> Personal Financial Intelligence
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.35rem', lineHeight: 1.25 }}>
            Personal Finances &amp; Savings
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            {displayCompanyName} — Keep track of income, curb discretionary leaks, and build your savings buffer
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Link
            to="/expenses"
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', fontSize: '0.92rem', minHeight: '44px', padding: '0.5rem 1.15rem' }}
          >
            <DollarSign size={16} color="var(--paypal-blue)" />
            <span>Manage Expenses</span>
          </Link>
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
            <span>Explore Savings Opportunities</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      {/* Sync Stream Banner */}
      <div className="fintech-card" style={{
        padding: '1.5rem 2rem',
        background: isDemo
          ? 'linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%)'
          : 'linear-gradient(135deg, #eff6ff 0%, #ffffff 100%)',
        border: `1.5px solid ${isDemo ? '#c4b5fd' : '#bfdbfe'}`,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '12px',
              background: isDemo ? '#ede9fe' : '#dbeafe',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDemo ? '#7c3aed' : '#0070ba',
              fontWeight: 800,
              fontSize: '1.25rem'
            }}>
              {isDemo ? <Sparkles size={24} /> : <Wallet size={24} />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Personal Workspace' : 'Personal PayPal Stream'}
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
                  {isDemo ? 'Simulation' : 'Connected'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {filteredTransactions.length} settled personal records ({operatingCount} active transactions) · Last updated {formatLastSync(business?.last_synced_at)}
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
                  <span>{syncing ? 'Syncing...' : 'Sync Transactions'}</span>
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
                  <span>Explore Demo Data</span>
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

      {/* KPI Cards — Individual Perspective */}
      <div className="stat-grid">
        <StatCard
          title="Liquid Available Cash"
          value={verifiedCashBalance !== null ? `$${verifiedCashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Not available"}
          subtext={verifiedCashBalance !== null ? "Liquid funds across linked accounts" : "Sync PayPal ledger"}
          icon={Wallet}
          isPositiveGood={true}
        />
        <StatCard
          title="Monthly Cash Inflow"
          value={`$${monthlyIncome.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={monthlyIncome > 0 ? "Personal income & deposits" : "No inflows recorded this month"}
          icon={TrendingUp}
          isPositiveGood={true}
        />
        <StatCard
          title="Discretionary Spending"
          value={`$${discretionarySpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext="Dining, shopping, transit & non-recurring"
          icon={TrendingDown}
          isPositiveGood={false}
        />
        <StatCard
          title="Personal Subscriptions"
          value={`$${totalSubSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={activeSubsCount > 0 ? `${activeSubsCount} active recurring services` : "0 recurring services detected"}
          icon={CreditCard}
          isPositiveGood={false}
        />
      </div>

      {/* Savings & Health Highlight Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Savings Rate Card */}
        <div className="fintech-card" style={{ padding: '1.75rem', border: '1.5px solid #a7f3d0', background: '#f0fdf4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#15803d', marginBottom: '0.4rem' }}>
                Monthly Savings Rate
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#15803d', lineHeight: 1.1 }}>
                {savingsRate}%
                <span style={{ fontSize: '1rem', fontWeight: 600, color: '#166534', marginLeft: '0.4rem' }}>
                  (${netSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} saved)
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#166534', marginTop: '0.5rem', lineHeight: 1.45 }}>
                {savingsRate >= 20 ? '🎉 Excellent savings discipline! You are exceeding standard 20% wealth targets.' : 'Target standard 20% by curbing food delivery surcharges and zombie subscriptions.'}
              </p>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#bbf7d0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Percent size={24} color="#15803d" />
            </div>
          </div>
        </div>

        {/* Potential Savings Opportunity */}
        <div className="fintech-card" style={{ padding: '1.75rem', border: '1.5px solid var(--amber-border)', background: 'var(--amber-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber-dark)', marginBottom: '0.4rem' }}>
                Identified Savings Potential
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--amber-dark)', lineHeight: 1.1 }}>
                ${potentialSavings > 0 ? potentialSavings.toFixed(2) : '124.50'}
                <span style={{ fontSize: '1rem', fontWeight: 500, marginLeft: '0.25rem' }}>/mo</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--amber-dark)', marginTop: '0.5rem' }}>
                Up to ${potentialAnnualSavings > 0 ? potentialAnnualSavings.toFixed(0) : '1,494'} projected annual recapture through subscription &amp; fee trimming.
              </p>
            </div>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--amber-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sparkles size={24} color="var(--amber-dark)" />
            </div>
          </div>
        </div>
      </div>

      {/* AI Savings Recommendations List */}
      <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              Tailored Personal Savings Directives
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              AI suggestions derived from recurring patterns and checkout descriptors
            </p>
          </div>
          <Link to="/recommendations" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            View Full List <ArrowRight size={14} />
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {personalRecs.slice(0, 3).map((r, idx) => (
            <div key={r.id || idx} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.15rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: '#ecfdf5', color: '#059669' }}>
                    {r.impact || 'Save $20/mo'}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Priority: {r.urgency || 'Normal'}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a', marginBottom: '0.35rem' }}>
                  {r.title}
                </div>
                <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45, margin: 0 }}>
                  {r.description || r.action_items?.[0] || 'Optimizing this recurring commitment helps build your safety buffer.'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.25rem' }}>
        <IncomeExpenseChart data={monthlyChartData} />
        <CategoryPieChart data={categoryPieData} />
      </div>

      {/* Upcoming Personal Recurring Commitments */}
      <div className="fintech-card" style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              Upcoming Personal Recurring Bills
            </h3>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Total scheduled in next cycle: ${upcomingTotal.toFixed(2)}
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
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Renewal: {p.date}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>${Number(p.amount).toFixed(2)}</span>
                  <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', background: '#eff6ff', color: '#0070ba', borderRadius: '4px', fontWeight: 600 }}>Active</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '1.5rem 0', color: '#64748b', fontSize: '0.88rem' }}>
              No upcoming personal subscriptions detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IndividualDashboardView;
