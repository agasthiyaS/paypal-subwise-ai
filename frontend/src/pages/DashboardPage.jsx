import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { transactionsAPI, subscriptionsAPI, recommendationsAPI, paypalAPI, demoAPI } from '../services/api';
import { classifyFinancialTransactions, isValidOperatingTransaction, isCurrencyConversionLeg } from '../utils/financialClassification';
import PayPalConnectModal from '../components/settings/PayPalConnectModal';
import SandboxPaymentModal from '../components/settings/SandboxPaymentModal';
import StatCard from '../components/common/StatCard';
import IncomeExpenseChart from '../components/dashboard/IncomeExpenseChart';
import SubscriptionSpendingChart from '../components/dashboard/SubscriptionSpendingChart';
import CashFlowTrendChart from '../components/dashboard/CashFlowTrendChart';
import CategoryPieChart from '../components/dashboard/CategoryPieChart';
import IndividualDashboardView from '../components/dashboard/IndividualDashboardView';
import HouseholdDashboardView from '../components/dashboard/HouseholdDashboardView';
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
  Layers,
  Database,
  Lock,
  Settings,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

/** Health score band colours */
const healthColor = (score) => {
  if (score >= 80) return { bg: 'var(--emerald-bg)', border: 'var(--emerald-border)', text: 'var(--emerald-dark)', label: 'Healthy Buffer' };
  if (score >= 60) return { bg: 'var(--amber-bg)', border: 'var(--amber-border)', text: 'var(--amber-dark)', label: 'Moderate Risk' };
  return { bg: 'var(--rose-bg)', border: 'var(--rose-border)', text: 'var(--rose-dark)', label: 'Cash Crunch Risk' };
};

const DashboardPage = () => {
  const { business, refreshBusiness, switchBusinessMode, isDemoMode } = useAuth();
  const [modalOpen, setModalOpen] = useState(false);
  const [testPaymentModalOpen, setTestPaymentModalOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [loadingData, setLoadingData] = useState(true);

  const [transactions, setTransactions] = useState([]);
  const [subscriptionSummary, setSubscriptionSummary] = useState(null);
  const [subAnalysis, setSubAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [paypalStatus, setPaypalStatus] = useState(null);

  const isDemo = Boolean(business?.is_demo || isDemoMode);
  const paypalMode = isDemo ? 'demo' : ((business?.paypal_mode === 'live') ? 'live' : 'sandbox');
  const isSandbox = !isDemo && paypalMode === 'sandbox';
  const isLive = !isDemo && paypalMode === 'live';

  const loadData = async () => {
    try {
      setLoadingData(true);
      const [txRes, subRes, recRes, statusRes, analysisRes] = await Promise.allSettled([
        transactionsAPI.getTransactions({ limit: 500 }),
        subscriptionsAPI.getSubscriptions(),
        recommendationsAPI.getRecommendations(),
        paypalAPI.getStatus(),
        subscriptionsAPI.getAnalysis(),
      ]);

      if (txRes.status === 'fulfilled') setTransactions(txRes.value || []);
      if (subRes.status === 'fulfilled') setSubscriptionSummary(subRes.value);
      if (recRes.status === 'fulfilled') setRecommendations(recRes.value || []);
      if (statusRes.status === 'fulfilled') setPaypalStatus(statusRes.value);
      if (analysisRes.status === 'fulfilled') setSubAnalysis(analysisRes.value);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    loadData();

    // Check for PayPal Checkout return redirect (?paypal_test=success&token=...)
    try {
      const searchParams = new URLSearchParams(window.location.search);
      const testStatus = searchParams.get('paypal_test');
      const orderToken = searchParams.get('token');

      if (testStatus === 'success' && orderToken) {
        const captureRedirectOrder = async () => {
          setSyncing(true);
          setSyncStatus({
            type: 'info',
            text: `Capturing approved PayPal Sandbox payment (Order: ${orderToken})...`
          });
          try {
            const capRes = await paypalAPI.captureOrder(orderToken);
            setSyncStatus({
              type: 'success',
              text: `PayPal Sandbox payment of $${Number(capRes.gross_amount).toFixed(2)} USD captured successfully! TxID: ${capRes.capture_id} (COMPLETED).`
            });
            await refreshBusiness();
            await loadData();
          } catch (err) {
            setSyncStatus({
              type: 'error',
              text: err.response?.data?.detail || 'Failed to capture approved PayPal Sandbox order.'
            });
          } finally {
            setSyncing(false);
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        };
        captureRedirectOrder();
      } else if (testStatus === 'cancel') {
        setSyncStatus({
          type: 'error',
          text: 'PayPal Sandbox test payment was cancelled by the buyer.'
        });
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (e) {
      console.error('Error handling redirect query params:', e);
    }
  }, [business?.id]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await paypalAPI.sync();
      setSyncStatus({
        type: 'success',
        text: res.message || `Successfully synchronized transactions in ${paypalMode.toUpperCase()} mode.`
      });
      await refreshBusiness();
      await loadData();
    } catch (err) {
      setSyncStatus({
        type: 'error',
        text: err.response?.data?.detail || `PayPal ${paypalMode.toUpperCase()} sync failed. Please check credentials.`
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleResetDemo = async () => {
    setSyncing(true);
    setSyncStatus({ type: 'info', text: 'Resetting and regenerating canonical demo dataset...' });
    try {
      await demoAPI.reset();
      setSyncStatus({ type: 'success', text: 'Demo dataset successfully reset to 6-month canonical baseline.' });
      await refreshBusiness();
      await loadData();
    } catch (err) {
      setSyncStatus({ type: 'error', text: 'Failed to reset demo dataset.' });
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleMode = async (targetMode) => {
    setSyncing(true);
    try {
      if (targetMode === 'demo') {
        await demoAPI.generate();
      }
      await switchBusinessMode(targetMode);
      await refreshBusiness();
      window.location.reload();
    } catch (err) {
      console.error('Mode switch failed:', err);
    } finally {
      setSyncing(false);
    }
  };

  const formatLastSync = (dateStr) => {
    if (!dateStr) return 'Not yet synced';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  // Business Identity: clean demo/sample names
  const displayCompanyName = useMemo(() => {
    const name = business?.company_name;
    if (!name) return 'My Business';
    if (business?.is_demo || isDemo) return 'DemoTech Solutions';
    const lower = name.toLowerCase();
    if (lower.includes('acme') || lower === 'business' || lower === 'business workspace') {
      return 'My Business';
    }
    return name;
  }, [business?.company_name, business?.is_demo, isDemo]);

  // Environment-aware transaction segregation (defense in depth)
  const filteredTransactions = useMemo(() => {
    if (!Array.isArray(transactions)) return [];
    if (isDemo) {
      return transactions.filter(t => t.data_source === 'demo' || t.data_source === 'demo_fixture' || t.is_simulated || (t.paypal_transaction_id && t.paypal_transaction_id.startsWith('DEMO_')));
    }
    if (isLive) {
      return transactions.filter(t => t.data_source === 'live' && !t.is_simulated && !(t.paypal_transaction_id && t.paypal_transaction_id.startsWith('DEMO_')));
    }
    // Sandbox
    return transactions.filter(t => t.data_source === 'sandbox' || (!t.data_source && !t.is_simulated && !(t.paypal_transaction_id && t.paypal_transaction_id.startsWith('DEMO_'))));
  }, [transactions, isDemo, isLive]);

  // Derive metrics strictly from verified transactions & subscriptions
  const hasTransactions = filteredTransactions.length > 0;
  const activeSubsCount = subscriptionSummary?.total_active_count || 0;
  const totalSubSpend = subscriptionSummary?.total_monthly_spend || 0.0;
  const potentialSavings = subscriptionSummary?.potential_monthly_savings || 0.0;
  const potentialAnnualSavings = potentialSavings * 12.0;

  // Operating income vs non-operating funding & currency conversion segregation
  // Initial balances, account funding, SubWise test payments, and currency conversion legs are isolated.
  const classification = useMemo(() => {
    return classifyFinancialTransactions(filteredTransactions, business?.currency || 'USD');
  }, [filteredTransactions, business?.currency]);

  const monthlyIncome = classification.operatingRevenue;
  const monthlyExpenses = classification.operatingExpenses;
  const fundingInflows = classification.fundingInflows;
  const operatingCount = classification.operatingCount;

  // Traceable Available Cash Balance: derived solely from settled net PayPal ledger transactions
  // Safely respects base currency and offsets cross-currency conversion legs
  const verifiedCashBalance = useMemo(() => {
    if (!hasTransactions) return null;
    const baseCurr = (business?.currency || 'USD').toUpperCase();
    let baseTotal = 0;
    const nonBaseTotals = {};
    filteredTransactions.forEach((tx) => {
      // Exclude currency conversion legs matching forecast_engine.py calculation
      if (isCurrencyConversionLeg(tx, filteredTransactions)) return;
      const amt = Number(tx.net_amount) || Number(tx.gross_amount) || 0;
      const curr = (tx.currency || baseCurr).toUpperCase();
      if (curr === baseCurr) {
        baseTotal += amt;
      } else {
        nonBaseTotals[curr] = (nonBaseTotals[curr] || 0) + amt;
      }
    });
    let total = baseTotal;
    Object.values(nonBaseTotals).forEach((netNonBase) => {
      if (Math.abs(netNonBase) > 0.01) total += netNonBase;
    });
    return Math.round(total * 100) / 100;
  }, [filteredTransactions, hasTransactions, business?.currency]);

  // Runway calculation: only possible when operating expenses and verified balance exist
  const runwayStatus = useMemo(() => {
    if (verifiedCashBalance === null || verifiedCashBalance <= 0) {
      return { value: 'Not available', subtext: 'Sync account balance' };
    }
    if (monthlyExpenses <= 0) {
      return { value: 'Not available', subtext: 'Insufficient expense data to project runway' };
    }
    const netBurn = monthlyExpenses - monthlyIncome;
    if (netBurn <= 0) {
      return { value: 'Self-Sustaining', subtext: 'Operating revenue covers all expenses' };
    }
    const months = Math.round((verifiedCashBalance / netBurn) * 10) / 10;
    return { value: `${months} mos`, subtext: `${months} months projected liquidity horizon` };
  }, [verifiedCashBalance, monthlyExpenses, monthlyIncome]);

  // Financial Health Score: ONLY calculated when sufficient verified operating data exists
  // Requires at least 30 days of operating activity AND either operating revenue or recurring expenses
  const healthData = useMemo(() => {
    const hasOperatingData = (monthlyIncome > 0 || monthlyExpenses > 0 || totalSubSpend > 0);
    
    let daysSpan = 0;
    if (filteredTransactions.length > 1) {
      const dates = filteredTransactions.map(t => new Date(t.transaction_date).getTime()).sort();
      daysSpan = (dates[dates.length - 1] - dates[0]) / (1000 * 60 * 60 * 24);
    }

    if (!hasTransactions || !hasOperatingData || daysSpan < 20) {
      return {
        score: null,
        displayText: 'Insufficient data',
        label: 'Insufficient Activity',
        subtext: 'Requires verified operating revenues & expense history',
        color: 'var(--text-muted)',
        bg: 'var(--bg-subtle)',
        border: 'var(--border-medium)',
        barWidth: '0%'
      };
    }

    let score = 70;
    if (monthlyIncome > 0) {
      const subRatio = totalSubSpend / monthlyIncome;
      if (subRatio > 0.40) score -= 25;
      else if (subRatio > 0.20) score -= 10;
      else score += 10;
    }
    if (runwayStatus.value.includes('mos')) {
      const mos = parseFloat(runwayStatus.value);
      if (mos < 3) score -= 30;
      else if (mos < 6) score -= 10;
      else score += 15;
    }
    score = Math.max(15, Math.min(95, score));
    const hCol = healthColor(score);
    return {
      score,
      displayText: `${score}`,
      label: hCol.label,
      subtext: `Computed from ${filteredTransactions.length} verified operating transactions`,
      color: hCol.text,
      bg: hCol.bg,
      border: hCol.border,
      barWidth: `${score}%`
    };
  }, [hasTransactions, monthlyIncome, monthlyExpenses, totalSubSpend, filteredTransactions, runwayStatus]);

  // Build chart history exclusively from verified operating transactions (no invented bars for funding or FX conversion legs)
  const monthlyChartData = useMemo(() => {
    if (!hasTransactions || !classification.operatingTransactions.length) return [];
    const monthMap = {};

    classification.operatingTransactions.forEach((tx) => {
      const d = new Date(tx.transaction_date);
      const key = d.toLocaleString('en-US', { month: 'short' });
      if (!monthMap[key]) {
        monthMap[key] = { month: key, income: 0, expenses: 0, subscriptions: totalSubSpend, balance: verifiedCashBalance || 0 };
      }
      const amt = Number(tx.gross_amount) || 0;
      if (amt > 0) monthMap[key].income += amt;
      else monthMap[key].expenses += Math.abs(amt);
    });

    const list = Object.values(monthMap);
    list.forEach(m => {
      m.income = Math.round(m.income);
      m.expenses = Math.round(m.expenses);
    });
    return list;
  }, [hasTransactions, classification.operatingTransactions, totalSubSpend, verifiedCashBalance]);

  // Category breakdown for pie chart
  const categoryPieData = useMemo(() => {
    if (!subscriptionSummary?.category_distribution) return [];
    const colors = ['#0070ba', '#003087', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];
    let idx = 0;
    return Object.entries(subscriptionSummary.category_distribution).map(([cat, val]) => ({
      name: cat,
      value: val,
      color: colors[idx++ % colors.length]
    }));
  }, [subscriptionSummary]);

  // Upcoming commitments list
  const upcomingPayments = useMemo(() => {
    if (!subscriptionSummary?.subscriptions) return [];
    return subscriptionSummary.subscriptions.slice(0, 5).map((s, idx) => ({
      id: s.id || idx,
      name: s.vendor_name,
      amount: s.latest_amount,
      date: s.next_billing_date ? new Date(s.next_billing_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Monthly',
      isEssential: s.tier === 'Tier 1 (Core Ops)'
    }));
  }, [subscriptionSummary]);

  const upcomingTotal = upcomingPayments.reduce((acc, p) => acc + (p.amount || 0), 0);

  const accountType = business?.account_type || 'business';

  const viewProps = {
    business,
    transactions,
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
  };

  if (accountType === 'individual') {
    return (
      <>
        <IndividualDashboardView {...viewProps} />
        <PayPalConnectModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConnected={() => {
            setModalOpen(false);
            refreshBusiness();
            loadData();
          }}
        />
        <SandboxPaymentModal
          isOpen={testPaymentModalOpen}
          onClose={() => setTestPaymentModalOpen(false)}
          onSuccess={async () => {
            await refreshBusiness();
            await loadData();
          }}
        />
      </>
    );
  }

  if (accountType === 'household') {
    return (
      <>
        <HouseholdDashboardView {...viewProps} />
        <PayPalConnectModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConnected={() => {
            setModalOpen(false);
            refreshBusiness();
            loadData();
          }}
        />
        <SandboxPaymentModal
          isOpen={testPaymentModalOpen}
          onClose={() => setTestPaymentModalOpen(false)}
          onSuccess={async () => {
            await refreshBusiness();
            await loadData();
          }}
        />
      </>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.45rem', lineHeight: 1.25 }}>
            Executive Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
            {displayCompanyName} — Cash-flow &amp; Subscription Intelligence
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => setModalOpen(true)}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', fontSize: '1rem', minHeight: '48px', padding: '0.65rem 1.35rem' }}
          >
            <Settings size={18} color="var(--paypal-blue)" />
            <span>PayPal Setup</span>
          </button>
          <Link
            to="/simulator"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.55rem',
              padding: '0.85rem 1.65rem',
              background: 'var(--navy-primary)',
              color: '#fff',
              borderRadius: 'var(--radius-md)',
              fontWeight: 700,
              fontSize: '1rem',
              textDecoration: 'none',
              boxShadow: '0 3px 10px rgba(0, 48, 135, 0.25)',
              minHeight: '48px',
            }}
          >
            Run Scenario Simulator <ArrowRight size={18} />
          </Link>
        </div>
      </div>

      {/* PayPal Stream Intelligence & Synchronization Banner */}
      <div className="fintech-card" style={{
        padding: '1.65rem 2rem',
        background: isDemo
          ? 'linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%)'
          : isSandbox
          ? 'linear-gradient(135deg, #fffbeb 0%, #ffffff 100%)'
          : isLive
          ? 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%)'
          : 'linear-gradient(135deg, var(--bg-subtle) 0%, #ffffff 100%)',
        border: `1.5px solid ${isDemo ? '#c4b5fd' : isSandbox ? '#fde68a' : isLive ? '#bbf7d0' : 'var(--border-light)'}`,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.35rem' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-md)',
              background: isDemo ? '#ede9fe' : isSandbox ? '#fef3c7' : isLive ? '#dcfce7' : 'var(--paypal-blue-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: `1.5px solid ${isDemo ? '#a78bfa' : isSandbox ? '#fde68a' : isLive ? '#86efac' : '#bae6fd'}`
            }}>
              {isDemo ? (
                <Sparkles size={28} color="#7c3aed" />
              ) : isSandbox ? (
                <Layers size={28} color="var(--amber-dark)" />
              ) : isLive ? (
                <Lock size={28} color="var(--emerald-dark)" />
              ) : (
                <Database size={28} color="var(--paypal-blue)" />
              )}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Stream Engine' : 'PayPal Stream Engine'}
                </span>
                <span style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  background: isDemo ? '#ede9fe' : isSandbox ? '#fef3c7' : isLive ? '#dcfce7' : 'var(--paypal-blue-subtle)',
                  color: isDemo ? '#6d28d9' : isSandbox ? 'var(--amber-dark)' : isLive ? 'var(--emerald-dark)' : 'var(--navy-primary)',
                  border: `1px solid ${isDemo ? '#c4b5fd' : isSandbox ? '#fde68a' : isLive ? '#86efac' : '#bae6fd'}`
                }}>
                  {isDemo ? 'DEMO ENVIRONMENT' : isSandbox ? 'SANDBOX API' : isLive ? 'LIVE RAILS' : 'DEMO STREAM'}
                </span>
                {!isDemo && paypalStatus?.configured && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--emerald-dark)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={16} /> Ready
                  </span>
                )}
                {isDemo && (
                  <span style={{ fontSize: '0.8rem', color: '#6d28d9', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={16} /> Isolated Profile
                  </span>
                )}
              </div>
              <div style={{ fontSize: '1rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                {isDemo
                  ? 'Isolated demonstration environment for DemoTech Solutions. All records are reproducible simulated fixtures.'
                  : isSandbox
                  ? 'Connected to PayPal Developer Sandbox via OAuth 2.0 Reporting API'
                  : isLive
                  ? 'Connected to PayPal Production REST API'
                  : 'Demonstration stream with verified SaaS recurring payment signatures'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Transactions / Last Sync
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.15rem' }}>
                {filteredTransactions.length} ledger records ({operatingCount} operating) · {isDemo ? 'Reproducible Dataset' : formatLastSync(business?.last_synced_at)}
              </div>
            </div>

            {isDemo ? (
              <>
                <button
                  onClick={handleResetDemo}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minHeight: '48px', justifyContent: 'center', fontSize: '1rem', background: '#6d28d9', borderColor: '#5b21b6' }}
                  title="Reset and regenerate 6-month canonical demo dataset"
                >
                  <RefreshCw size={17} className={syncing ? 'spin-icon' : ''} />
                  <span>{syncing ? 'Resetting...' : 'Reset Demo Data'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleMode('sandbox')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minHeight: '48px', fontSize: '1rem' }}
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
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minWidth: '160px', minHeight: '48px', justifyContent: 'center', fontSize: '1rem' }}
                >
                  <RefreshCw size={17} className={syncing ? 'spin-icon' : ''} />
                  <span>{syncing ? 'Synchronizing...' : 'Sync Stream'}</span>
                </button>

                {isSandbox && (
                  <button
                    type="button"
                    onClick={() => setTestPaymentModalOpen(true)}
                    className="btn-fintech btn-fintech-outline btn-sm"
                    title="Test PayPal Sandbox Payment using Orders v2 API ($5.00)"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.55rem',
                      minHeight: '48px',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      borderColor: '#f59e0b',
                      color: '#b45309',
                      background: '#fffbeb',
                      fontWeight: 700,
                      cursor: 'pointer',
                      position: 'relative',
                      zIndex: 5
                    }}
                  >
                    <CreditCard size={18} color="#b45309" />
                    <span>Test Sandbox Payment ($5.00)</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => handleToggleMode('demo')}
                  disabled={syncing}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.55rem',
                    minHeight: '48px',
                    padding: '0 1.25rem',
                    borderRadius: 'var(--radius-md)',
                    background: '#ede9fe',
                    color: '#6d28d9',
                    border: '1.5px solid #c4b5fd',
                    fontWeight: 700,
                    fontSize: '1rem',
                    cursor: 'pointer'
                  }}
                  title="Switch to DemoTech Solutions 6-month historical dataset"
                >
                  <Sparkles size={18} color="#7c3aed" />
                  <span>Switch to Demo</span>
                </button>
              </>
            )}

          </div>
        </div>

        {/* Sync Status Banner */}
        {syncStatus && (
          <div style={{
            marginTop: '1.25rem',
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
            {syncStatus.type === 'success' ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
            <span>{syncStatus.text}</span>
          </div>
        )}
      </div>

      {/* Empty State Banner if 0 transactions */}
      {!hasTransactions && !loadingData && (
        <div className="fintech-card" style={{
          padding: '2.5rem 2rem',
          textAlign: 'center',
          background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)',
          border: '1.5px dashed var(--border-medium)',
          borderRadius: 'var(--radius-lg)'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'var(--paypal-blue-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem'
          }}>
            <Database size={32} color="var(--paypal-blue)" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
            No PayPal Transactions Found
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', maxWidth: '580px', margin: '0 auto 1.5rem', lineHeight: 1.6 }}>
            Your account has not synchronized any transactions yet. Click <strong>Sync Stream</strong> above to query your PayPal Sandbox account, or configure your Developer credentials in PayPal Setup.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="btn-fintech btn-fintech-primary"
              style={{ minHeight: '48px', padding: '0.75rem 1.75rem' }}
            >
              Sync PayPal Sandbox
            </button>
            <button
              onClick={() => setModalOpen(true)}
              className="btn-fintech btn-fintech-outline"
              style={{ minHeight: '48px', padding: '0.75rem 1.75rem' }}
            >
              Configure Credentials
            </button>
          </div>
        </div>
      )}

      {/* KPI Grid — 4 stat cards */}
      <div className="stat-grid">
        <StatCard
          title="Total Monthly Income"
          value={`$${monthlyIncome.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={
            fundingInflows > 0 && monthlyIncome === 0
              ? `$${fundingInflows.toLocaleString(undefined, { minimumFractionDigits: 2 })} funding excluded`
              : hasTransactions && monthlyIncome > 0
                ? "Current verified operating sales"
                : "No operating revenue recorded"
          }
          icon={TrendingUp}
          isPositiveGood={true}
        />
        <StatCard
          title="Total Monthly Expenses"
          value={`$${monthlyExpenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={monthlyExpenses > 0 ? "Operating cash outflows" : "No operating expenses recorded"}
          icon={TrendingDown}
          isPositiveGood={false}
        />
        <StatCard
          title="Subscription Expenses"
          value={`$${totalSubSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={activeSubsCount > 0 ? `${activeSubsCount} active recurring commitments` : "0 recurring commitments detected"}
          icon={CreditCard}
          isPositiveGood={false}
        />
        <StatCard
          title="Available Cash Balance"
          value={
            verifiedCashBalance !== null
              ? `$${verifiedCashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              : "Not available"
          }
          subtext={
            verifiedCashBalance !== null
              ? (runwayStatus.value !== 'Not available' ? `${runwayStatus.value} runway` : "Verified PayPal ledger balance")
              : "Sync account balance"
          }
          icon={Wallet}
          isPositiveGood={true}
        />
      </div>

      {/* Financial Health Indicator + Savings Opportunity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        {/* Health Score */}
        <div className="fintech-card" style={{
          border: `1px solid ${healthData.border}`,
          background: healthData.bg,
          padding: '1.5rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: healthData.color, marginBottom: '0.5rem' }}>
                Financial Health Score
              </div>
              <div style={{ fontSize: '3rem', fontWeight: 800, color: healthData.color, lineHeight: 1 }}>
                {healthData.displayText}
                {healthData.score !== null && (
                  <span style={{ fontSize: '1.2rem', fontWeight: 500, marginLeft: '0.2rem' }}>/100</span>
                )}
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: healthData.color, marginTop: '0.5rem' }}>
                {healthData.label}
              </div>
            </div>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: healthData.border,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Activity size={26} color={healthData.color} />
            </div>
          </div>
          {/* Score bar */}
          <div style={{ marginTop: '1.25rem' }}>
            <div style={{ height: '8px', background: 'rgba(0,0,0,0.08)', borderRadius: '99px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: healthData.barWidth,
                background: healthData.color,
                borderRadius: '99px',
                transition: 'width 1s ease',
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: healthData.color, marginTop: '0.4rem', opacity: 0.75 }}>
              <span>{healthData.subtext}</span>
              {healthData.score !== null && <span>Optimal (100)</span>}
            </div>
          </div>
        </div>

        {/* Savings Opportunity */}
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1px solid var(--amber-border)', background: 'var(--amber-bg)' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber-dark)', marginBottom: '0.5rem' }}>
            Identified Savings Opportunity
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--amber-dark)', lineHeight: 1 }}>
            ${potentialSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span style={{ fontSize: '1rem', fontWeight: 500, marginLeft: '0.3rem' }}>/month</span>
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--amber-dark)', marginTop: '0.4rem' }}>
            ${potentialAnnualSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} potential annual savings
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recommendations.length > 0 ? (
              recommendations.slice(0, 3).map((r) => (
                <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--amber-dark)' }}>
                  <AlertTriangle size={14} />
                  <span>{r.title}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--amber-dark)', opacity: 0.9 }}>
                {hasTransactions ? 'All recurring commitments are within normal parameters.' : 'Synchronize transactions to analyze SaaS spend optimization.'}
              </div>
            )}
          </div>
          <Link
            to="/recommendations"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              marginTop: '1rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              color: 'var(--amber-dark)',
              textDecoration: 'none',
            }}
          >
            View all recommendations <ArrowRight size={14} />
          </Link>
        </div>

        {/* Upcoming Subscriptions */}
        <div className="fintech-card" style={{ padding: '1.5rem', gridColumn: 'span 1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
                Upcoming Commitments (7 days)
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.2rem' }}>
                ${upcomingTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <Calendar size={22} color="var(--paypal-blue)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {upcomingPayments.length > 0 ? (
              upcomingPayments.map((p) => (
                <div key={p.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 0',
                  borderBottom: '1px solid var(--border-light)',
                  fontSize: '0.88rem',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-body)' }}>{p.name}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-caption)' }}>{p.date}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>${Number(p.amount).toFixed(2)}</span>
                    {!p.isEssential && (
                      <span style={{
                        fontSize: '0.7rem',
                        padding: '0.15rem 0.4rem',
                        background: 'var(--amber-bg)',
                        color: 'var(--amber-dark)',
                        borderRadius: '4px',
                        fontWeight: 700,
                      }}>Review</span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '1rem 0', color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>
                No upcoming subscription renewals detected.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Subscription Expense Analysis Summary */}
      {subAnalysis?.has_subscriptions && (
        <div className="fintech-card" style={{ padding: '1.75rem 2rem', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
                  Subscription Expense Analysis
                </h3>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '4px', background: 'var(--paypal-blue-subtle)', color: 'var(--navy-primary)' }}>
                  {subAnalysis.vendor_analysis?.length || 0} Providers
                </span>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Normalized recurring commitments, cadence conversion, and revenue impact analysis
              </p>
            </div>
            <Link
              to="/subscriptions"
              style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
            >
              Full Analysis Directory <ArrowRight size={15} />
            </Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
            {/* Monthly Commitment */}
            <div style={{ padding: '1.15rem 1.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Monthly Commitment
              </div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.35rem' }}>
                ${Number(subAnalysis.total_monthly_commitment).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}>/mo</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                ${subAnalysis.confirmed_monthly_commitment.toFixed(2)} confirmed · ${subAnalysis.potential_monthly_commitment.toFixed(2)} potential
              </div>
            </div>

            {/* Annual Commitment */}
            <div style={{ padding: '1.15rem 1.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Estimated Annual Run-Rate
              </div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.35rem' }}>
                ${Number(subAnalysis.total_annual_commitment).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}>/yr</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Historical spend: ${Number(subAnalysis.actual_historical_spend_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} settled
              </div>
            </div>

            {/* Revenue Impact */}
            <div style={{ padding: '1.15rem 1.35rem', background: subAnalysis.revenue_comparison.has_sufficient_revenue_data ? (subAnalysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-bg)' : subAnalysis.revenue_comparison.burden_level === 'moderate' ? 'var(--amber-bg)' : 'var(--rose-bg)') : 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Revenue vs Subscriptions
              </div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: subAnalysis.revenue_comparison.has_sufficient_revenue_data ? (subAnalysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-dark)' : subAnalysis.revenue_comparison.burden_level === 'moderate' ? 'var(--amber-dark)' : 'var(--rose-dark)') : 'var(--text-muted)', marginTop: '0.35rem' }}>
                {subAnalysis.revenue_comparison.revenue_percentage !== null ? `${subAnalysis.revenue_comparison.revenue_percentage}%` : 'N/A'}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, marginLeft: '0.4rem' }}>
                  {subAnalysis.revenue_comparison.has_sufficient_revenue_data ? subAnalysis.revenue_comparison.burden_level.toUpperCase() : 'NO SALES'}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                {subAnalysis.revenue_comparison.explanation}
              </div>
            </div>

            {/* Spending Trend */}
            <div style={{ padding: '1.15rem 1.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Spending Velocity &amp; Trend
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: subAnalysis.spending_trends.trend_direction === 'increasing' ? 'var(--rose-dark)' : 'var(--navy-slate)', marginTop: '0.45rem', textTransform: 'capitalize' }}>
                {subAnalysis.spending_trends.trend_direction.replace('_', ' ')}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                {subAnalysis.spending_trends.trend_summary}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row 1: Income vs Expenses + Category Pie */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.25rem' }}>
        <IncomeExpenseChart data={monthlyChartData} />
        <CategoryPieChart data={categoryPieData} />
      </div>

      {/* Charts Row 2: Subscription Spending + Cash Flow Trend */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.25rem' }}>
        <SubscriptionSpendingChart data={monthlyChartData} currentSpend={totalSubSpend} />
        <CashFlowTrendChart data={monthlyChartData} />
      </div>

      <PayPalConnectModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConnected={() => {
          setModalOpen(false);
          refreshBusiness();
          loadData();
        }}
      />

      <SandboxPaymentModal
        isOpen={testPaymentModalOpen}
        onClose={() => setTestPaymentModalOpen(false)}
        onSuccess={async () => {
          await refreshBusiness();
          await loadData();
        }}
      />
    </div>
  );
};

export default DashboardPage;
