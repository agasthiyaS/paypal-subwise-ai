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
  Calendar,
  ArrowRight,
  Sparkles,
  Percent,
  Settings,
  RefreshCw,
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
  expenseSummary,
  unifiedIntelligence,
}) => {
  // Computed Personal Metrics
  const netSavings = Math.max(0, monthlyIncome - monthlyExpenses);
  const savingsRate = monthlyIncome > 0 ? Math.round((netSavings / monthlyIncome) * 100) : 0;
  const discretionarySpend = Math.max(0, monthlyExpenses - totalSubSpend);

  // Individual Recommendations strictly from backend
  const personalRecs = Array.isArray(recommendations) ? recommendations : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', background: '#eff6ff', color: 'var(--paypal-blue)', padding: '0.2rem 0.6rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.35rem' }}>
            <Sparkles size={12} /> Personal Intelligence
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--navy-slate)', letterSpacing: '-0.02em', marginBottom: '0.15rem' }}>
            Personal Finances &amp; Savings
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            {displayCompanyName} — Keep track of income, curb discretionary leaks, and build your savings buffer
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Link
            to="/expenses"
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem', minHeight: '36px', padding: '0.45rem 0.95rem' }}
          >
            <DollarSign size={15} color="var(--paypal-blue)" />
            <span>Manage Expenses</span>
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
            <span>Savings Advice</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Sync Stream Banner */}
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
              {isDemo ? <Sparkles size={18} /> : <Wallet size={18} />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Personal Workspace' : 'Personal PayPal Stream'}
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
                {filteredTransactions.length} settled personal records ({operatingCount} active transactions) · Last updated {formatLastSync(business?.last_synced_at)}
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
                  <span>{syncing ? 'Syncing...' : 'Sync Stream'}</span>
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

      {/* KPI Cards — Individual Perspective with Hero Card */}
      <div className="stat-grid">
        <StatCard
          title="Liquid Available Cash"
          value={verifiedCashBalance !== null ? `$${verifiedCashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Not available"}
          subtext={verifiedCashBalance !== null ? "Liquid funds across linked accounts" : "Sync PayPal ledger"}
          icon={Wallet}
          isPositiveGood={true}
          hero={true}
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
          subtext={activeSubsCount > 0 ? `${activeSubsCount} recurring services` : "0 recurring services"}
          icon={CreditCard}
          isPositiveGood={false}
        />
      </div>

      {/* Savings & Health Highlight Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {/* Savings Rate Card */}
        <div className="fintech-card" style={{ padding: '1.25rem', border: '1px solid #bbf7d0', background: '#f0fdf4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#15803d', marginBottom: '0.35rem' }}>
                Monthly Savings Rate
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#15803d', lineHeight: 1.1 }}>
                {savingsRate}%
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#166534', marginLeft: '0.35rem' }}>
                  (${netSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} saved)
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#166534', marginTop: '0.4rem', lineHeight: 1.45 }}>
                {savingsRate >= 20 ? '🎉 Excellent savings discipline! Exceeding 20% target.' : 'Target 20% by curbing discretionary surcharges and zombie subscriptions.'}
              </p>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#bbf7d0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Percent size={20} color="#15803d" />
            </div>
          </div>
        </div>

        {/* Potential Savings Opportunity */}
        <div className="fintech-card" style={{
          padding: '1.25rem',
          border: potentialSavings > 0 ? '1px solid var(--amber-border)' : '1px solid var(--border-light)',
          background: potentialSavings > 0 ? 'var(--amber-bg)' : 'var(--bg-surface)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: potentialSavings > 0 ? 'var(--amber-dark)' : 'var(--text-muted)',
                marginBottom: '0.35rem'
              }}>
                Identified Savings Potential
              </div>
              <div style={{
                fontSize: '2.2rem',
                fontWeight: 800,
                color: potentialSavings > 0 ? 'var(--amber-dark)' : 'var(--navy-slate)',
                lineHeight: 1.1
              }}>
                ${potentialSavings > 0 ? potentialSavings.toFixed(2) : '0.00'}
                <span style={{ fontSize: '0.85rem', fontWeight: 500, marginLeft: '0.2rem' }}>/mo</span>
              </div>
              <p style={{
                fontSize: '0.8rem',
                color: potentialSavings > 0 ? 'var(--amber-dark)' : 'var(--text-muted)',
                marginTop: '0.4rem'
              }}>
                {potentialSavings > 0
                  ? `Up to $${potentialAnnualSavings.toFixed(0)} projected annual recapture.`
                  : 'No recurring fee leaks or redundant subscriptions currently identified.'}
              </p>
            </div>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: potentialSavings > 0 ? 'var(--amber-border)' : 'var(--bg-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Sparkles size={20} color={potentialSavings > 0 ? 'var(--amber-dark)' : 'var(--text-muted)'} />
            </div>
          </div>
        </div>
      </div>

      {/* AI Savings Recommendations List */}
      <div className="fintech-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
              Tailored Personal Savings Directives
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
              AI suggestions derived from verified recurring records and expense commitments
            </p>
          </div>
          <Link to="/recommendations" style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            View Full List <ArrowRight size={13} />
          </Link>
        </div>

        {personalRecs.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
            {personalRecs.slice(0, 3).map((r, idx) => (
              <div key={r.id || idx} style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '0.95rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.12rem 0.45rem', borderRadius: '4px', background: '#ecfdf5', color: '#059669' }}>
                      {r.monthly_savings ? `Save $${Number(r.monthly_savings).toFixed(0)}/mo` : (r.impact || 'Optimization')}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>Priority: {r.priority || r.urgency || 'Normal'}</span>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
                    {r.title}
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-body)', lineHeight: 1.45, margin: 0 }}>
                    {r.explanation || r.description || r.recommended_action || (r.action_items && r.action_items[0]) || 'Review and optimize this recurring commitment.'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: '8px', border: '1px dashed var(--border-medium)' }}>
            <Sparkles size={24} color="#94a3b8" style={{ marginBottom: '0.35rem' }} />
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--navy-slate)', marginBottom: '0.2rem' }}>No Active Savings Directives</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '400px', margin: '0 auto 1rem' }}>
              Add your expenses or sync transactions to detect subscription overlaps, price creeping, or optimization opportunities.
            </div>
            <Link to="/expenses" className="btn-fintech btn-fintech-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.35rem 0.85rem', fontSize: '0.82rem' }}>
              <DollarSign size={13} /> Record Expenses
            </Link>
          </div>
        )}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1rem' }}>
        <IncomeExpenseChart data={monthlyChartData} />
        <CategoryPieChart data={categoryPieData} />
      </div>

      {/* Upcoming Personal Recurring Commitments */}
      <div className="fintech-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
              Upcoming Personal Recurring Bills
            </h3>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Total scheduled in next cycle: ${upcomingTotal.toFixed(2)}
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
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Renewal: {p.date}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span style={{ fontWeight: 750, fontSize: '0.9rem', color: 'var(--navy-slate)' }}>${Number(p.amount).toFixed(2)}</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.12rem 0.45rem', background: '#eff6ff', color: 'var(--paypal-blue)', borderRadius: '4px', fontWeight: 600 }}>Active</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '1.25rem 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              No upcoming personal subscriptions detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IndividualDashboardView;
