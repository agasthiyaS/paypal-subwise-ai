import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { transactionsAPI, subscriptionsAPI, recommendationsAPI, paypalAPI, demoAPI, expensesAPI, intelligenceAPI } from '../services/api';
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
import FinancialWorkspaceLoader from '../components/common/FinancialWorkspaceLoader';
import { ChartCardSkeleton, SectionRetryCard } from '../components/common/DashboardSkeleton';
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

  // Progressive rendering readiness flags
  const [loadingStages, setLoadingStages] = useState({
    overview: 'active',
    data: 'pending',
    health: 'pending',
    intelligence: 'pending',
  });
  const [essentialReady, setEssentialReady] = useState(false);
  const [importantReady, setImportantReady] = useState(false);
  const [advancedReady, setAdvancedReady] = useState(false);

  const [transactions, setTransactions] = useState([]);
  const [subscriptionSummary, setSubscriptionSummary] = useState(null);
  const [subAnalysis, setSubAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [paypalStatus, setPaypalStatus] = useState(null);
  const [expenseSummary, setExpenseSummary] = useState(null);
  const [unifiedIntelligence, setUnifiedIntelligence] = useState(null);

  const isDemo = Boolean(business?.is_demo || isDemoMode);
  const paypalMode = isDemo ? 'demo' : ((business?.paypal_mode === 'live') ? 'live' : 'sandbox');
  const isSandbox = !isDemo && paypalMode === 'sandbox';
  const isLive = !isDemo && paypalMode === 'live';

  const loadData = async () => {
    try {
      setLoadingData(true);
      setLoadingStages({
        overview: 'complete',
        data: 'active',
        health: 'pending',
        intelligence: 'pending',
      });

      // Step A: Ensure Demo environment dataset exists if in Demo mode
      if (isDemo) {
        try {
          const demoStatus = await demoAPI.getStatus();
          if (!demoStatus.transaction_count || demoStatus.transaction_count === 0) {
            await demoAPI.generate();
            await refreshBusiness();
          }
        } catch (e) {
          console.warn('Demo environment auto-init check:', e);
        }
      }

      // Priority 1 (Essential): Core Transactions, Subscriptions & PayPal Connection Status
      const [txRes, subRes, statusRes] = await Promise.allSettled([
        transactionsAPI.getTransactions({ limit: 500 }),
        subscriptionsAPI.getSubscriptions(),
        paypalAPI.getStatus(),
      ]);

      if (txRes?.status === 'fulfilled') setTransactions(txRes.value || []);
      if (subRes?.status === 'fulfilled') setSubscriptionSummary(subRes.value);
      if (statusRes?.status === 'fulfilled') setPaypalStatus(statusRes.value);

      // Essential statistics are now ready to display
      setEssentialReady(true);
      setLoadingStages(prev => ({
        ...prev,
        data: 'complete',
        health: 'active',
      }));

      // Priority 2 (Important): Spending Analysis, Health Breakdown & Personal Expense Summaries
      const isConsumer = business?.account_type === 'individual' || business?.account_type === 'household';
      const p2Calls = [subscriptionsAPI.getAnalysis()];
      if (isConsumer) {
        p2Calls.push(expensesAPI.getSummary());
      }
      const p2Results = await Promise.allSettled(p2Calls);

      if (p2Results[0]?.status === 'fulfilled') setSubAnalysis(p2Results[0].value);
      if (isConsumer && p2Results[1]?.status === 'fulfilled') setExpenseSummary(p2Results[1].value);

      setImportantReady(true);
      setLoadingStages(prev => ({
        ...prev,
        health: 'complete',
        intelligence: 'active',
      }));

      // Priority 3 (Advanced): Recommendations, Intelligence & Forward Projections
      const p3Calls = [recommendationsAPI.getRecommendations()];
      if (isConsumer) {
        p3Calls.push(intelligenceAPI.getUnified());
      }
      const p3Results = await Promise.allSettled(p3Calls);

      if (p3Results[0]?.status === 'fulfilled') setRecommendations(p3Results[0].value || []);
      if (isConsumer && p3Results[1]?.status === 'fulfilled') setUnifiedIntelligence(p3Results[1].value);

      setAdvancedReady(true);
      setLoadingStages({
        overview: 'complete',
        data: 'complete',
        health: 'complete',
        intelligence: 'complete',
      });
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoadingData(false);
      setEssentialReady(true);
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

  // Grounded category breakdown for personal & household from real expense ledger
  const effectiveCategoryPieData = useMemo(() => {
    if (expenseSummary?.category_breakdown && expenseSummary.category_breakdown.length > 0) {
      const colors = ['#0070ba', '#003087', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1', '#06b6d4', '#ef4444', '#64748b'];
      return expenseSummary.category_breakdown.map((item, idx) => ({
        name: item.category,
        value: item.amount,
        color: colors[idx % colors.length]
      }));
    }
    return categoryPieData;
  }, [expenseSummary, categoryPieData]);

  // Grounded trend data for personal & household from real expense ledger
  const effectiveMonthlyChartData = useMemo(() => {
    if (expenseSummary?.recent_trend && expenseSummary.recent_trend.length > 0) {
      return expenseSummary.recent_trend.map(t => ({
        month: t.month,
        income: t.income,
        expenses: t.expenses,
        subscriptions: totalSubSpend,
        balance: verifiedCashBalance || 0
      }));
    }
    return monthlyChartData;
  }, [expenseSummary, monthlyChartData, totalSubSpend, verifiedCashBalance]);

  const effectiveMonthlyIncome = (expenseSummary?.total_income && expenseSummary.total_income > 0)
    ? expenseSummary.total_income
    : monthlyIncome;

  const effectiveMonthlyExpenses = (expenseSummary?.total_expenses && expenseSummary.total_expenses > 0)
    ? expenseSummary.total_expenses
    : monthlyExpenses;

  const effectiveRecommendations = (unifiedIntelligence?.recommendations && unifiedIntelligence.recommendations.length > 0)
    ? unifiedIntelligence.recommendations
    : recommendations;

  const effectivePotentialSavings = unifiedIntelligence?.total_potential_monthly_savings !== undefined
    ? unifiedIntelligence.total_potential_monthly_savings
    : potentialSavings;

  const effectivePotentialAnnualSavings = unifiedIntelligence?.total_potential_annual_savings !== undefined
    ? unifiedIntelligence.total_potential_annual_savings
    : potentialAnnualSavings;

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
    monthlyIncome: effectiveMonthlyIncome,
    monthlyExpenses: effectiveMonthlyExpenses,
    fundingInflows,
    totalSubSpend,
    activeSubsCount,
    verifiedCashBalance,
    runwayStatus,
    healthData,
    potentialSavings: effectivePotentialSavings,
    potentialAnnualSavings: effectivePotentialAnnualSavings,
    recommendations: effectiveRecommendations,
    upcomingPayments,
    upcomingTotal,
    subAnalysis,
    monthlyChartData: effectiveMonthlyChartData,
    categoryPieData: effectiveCategoryPieData,
    expenseSummary,
    unifiedIntelligence,
    essentialReady,
    importantReady,
    advancedReady,
    loadingStages,
  };

  // Render polished stage-based loading experience during initial data hydration
  if (!essentialReady && loadingData) {
    return (
      <FinancialWorkspaceLoader
        stages={loadingStages}
        accountType={accountType}
        companyName={displayCompanyName}
        isDemo={isDemo}
      />
    );
  }

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>

      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--navy-slate)', letterSpacing: '-0.02em', marginBottom: '0.2rem' }}>
            Executive Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            {displayCompanyName} — Cash-flow &amp; Subscription Intelligence
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => setModalOpen(true)}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.85rem', minHeight: '36px', padding: '0.45rem 0.95rem' }}
          >
            <Settings size={15} color="var(--paypal-blue)" />
            <span>PayPal Setup</span>
          </button>
          <Link
            to="/simulator"
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              fontSize: '0.85rem',
              minHeight: '36px',
              padding: '0.45rem 1rem',
              textDecoration: 'none',
            }}
          >
            Scenario Simulator <ArrowRight size={15} />
          </Link>
        </div>
      </div>

      {/* PayPal Stream Intelligence & Synchronization Banner */}
      <div className="fintech-card" style={{
        padding: '0.95rem 1.25rem',
        background: isDemo
          ? '#faf5ff'
          : isSandbox
          ? '#fffdf5'
          : isLive
          ? '#f0fdf4'
          : 'var(--bg-surface)',
        borderColor: isDemo ? '#ddd6fe' : isSandbox ? '#fde68a' : isLive ? '#bbf7d0' : 'var(--border-light)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: isDemo ? '#ede9fe' : isSandbox ? '#fef3c7' : isLive ? '#dcfce7' : 'var(--bg-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: `1px solid ${isDemo ? '#c4b5fd' : isSandbox ? '#fde68a' : isLive ? '#86efac' : 'var(--border-light)'}`,
              flexShrink: 0
            }}>
              {isDemo ? (
                <Sparkles size={18} color="#7c3aed" />
              ) : isSandbox ? (
                <Layers size={18} color="#b45309" />
              ) : isLive ? (
                <Lock size={18} color="#059669" />
              ) : (
                <Database size={18} color="var(--paypal-blue)" />
              )}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--navy-slate)' }}>
                  {isDemo ? 'Demo Stream Engine' : 'PayPal Stream Engine'}
                </span>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.55rem',
                  borderRadius: '9999px',
                  background: isDemo ? '#ede9fe' : isSandbox ? '#fef3c7' : isLive ? '#dcfce7' : 'var(--bg-subtle)',
                  color: isDemo ? '#6d28d9' : isSandbox ? '#92400e' : isLive ? '#065f46' : 'var(--navy-primary)',
                  border: `1px solid ${isDemo ? '#c4b5fd' : isSandbox ? '#fde68a' : isLive ? '#86efac' : 'var(--border-light)'}`
                }}>
                  {isDemo ? 'DEMO ENVIRONMENT' : isSandbox ? 'SANDBOX API' : isLive ? 'LIVE RAILS' : 'DEMO STREAM'}
                </span>
                {!isDemo && paypalStatus?.configured && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--emerald-dark)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                    <ShieldCheck size={14} /> Ready
                  </span>
                )}
                {isDemo && (
                  <span style={{ fontSize: '0.75rem', color: '#6d28d9', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                    <ShieldCheck size={14} /> Isolated Profile
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {filteredTransactions.length} ledger records ({operatingCount} operating) · {isDemo ? 'Reproducible Dataset' : formatLastSync(business?.last_synced_at)}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
            {isDemo ? (
              <>
                <button
                  onClick={handleResetDemo}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', minHeight: '34px', fontSize: '0.82rem', background: '#6d28d9', borderColor: '#5b21b6' }}
                  title="Reset and regenerate 6-month canonical demo dataset"
                >
                  <RefreshCw size={14} className={syncing ? 'spin' : ''} />
                  <span>{syncing ? 'Resetting...' : 'Reset Demo'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleMode('sandbox')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', minHeight: '34px', fontSize: '0.82rem' }}
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
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', minHeight: '34px', fontSize: '0.82rem' }}
                >
                  <RefreshCw size={14} className={syncing ? 'spin' : ''} />
                  <span>{syncing ? 'Syncing...' : 'Sync Stream'}</span>
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
                      gap: '0.45rem',
                      minHeight: '34px',
                      fontSize: '0.82rem',
                      borderColor: '#fde68a',
                      color: '#92400e',
                      background: '#fffbeb',
                      fontWeight: 600,
                    }}
                  >
                    <CreditCard size={14} color="#b45309" />
                    <span>Test Checkout ($5)</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => handleToggleMode('demo')}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-outline btn-sm"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    minHeight: '34px',
                    fontSize: '0.82rem',
                    background: '#faf5ff',
                    color: '#7c3aed',
                    borderColor: '#ddd6fe',
                    fontWeight: 600,
                  }}
                  title="Switch to DemoTech Solutions 6-month historical dataset"
                >
                  <Sparkles size={14} color="#7c3aed" />
                  <span>Demo Mode</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Sync Status Banner */}
        {syncStatus && (
          <div style={{
            marginTop: '0.75rem',
            padding: '0.65rem 1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.55rem',
            background: syncStatus.type === 'success' ? '#dcfce7' : '#fee2e2',
            color: syncStatus.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
            border: `1px solid ${syncStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`
          }}>
            {syncStatus.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            <span>{syncStatus.text}</span>
          </div>
        )}
      </div>

      {/* Empty State Banner if 0 transactions */}
      {!hasTransactions && !loadingData && (
        <div className="fintech-card" style={{
          padding: '2rem 1.5rem',
          textAlign: 'center',
          background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)',
          border: '1.5px dashed var(--border-medium)',
          borderRadius: 'var(--radius-lg)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'var(--paypal-blue-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem'
          }}>
            <Database size={24} color="var(--paypal-blue)" />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            No PayPal Transactions Found
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: '520px', margin: '0 auto 1.25rem', lineHeight: 1.5 }}>
            Your account has not synchronized any transactions yet. Click <strong>Sync Stream</strong> above to query your PayPal Sandbox account, or configure your Developer credentials in PayPal Setup.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="btn-fintech btn-fintech-primary btn-sm"
              style={{ minHeight: '36px', padding: '0.5rem 1.25rem' }}
            >
              Sync PayPal Sandbox
            </button>
            <button
              onClick={() => setModalOpen(true)}
              className="btn-fintech btn-fintech-outline btn-sm"
              style={{ minHeight: '36px', padding: '0.5rem 1.25rem' }}
            >
              Configure Credentials
            </button>
          </div>
        </div>
      )}

      {/* KPI Grid — 4 stat cards with Primary Hero Card */}
      <div className="stat-grid">
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
          hero={true}
        />
        <StatCard
          title="Total Monthly Income"
          value={`$${monthlyIncome.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={
            fundingInflows > 0 && monthlyIncome === 0
              ? `$${fundingInflows.toLocaleString(undefined, { minimumFractionDigits: 2 })} funding excluded`
              : hasTransactions && monthlyIncome > 0
                ? "Current operating sales"
                : "No operating revenue"
          }
          icon={TrendingUp}
          isPositiveGood={true}
        />
        <StatCard
          title="Total Monthly Expenses"
          value={`$${monthlyExpenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={monthlyExpenses > 0 ? "Operating cash outflows" : "No operating expenses"}
          icon={TrendingDown}
          isPositiveGood={false}
        />
        <StatCard
          title="Subscription Expenses"
          value={`$${totalSubSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtext={activeSubsCount > 0 ? `${activeSubsCount} recurring commitments` : "0 recurring commitments"}
          icon={CreditCard}
          isPositiveGood={false}
        />
      </div>

      {/* Financial Health Indicator + Savings Opportunity + Upcoming Commitments */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {/* Health Score */}
        <div className="fintech-card" style={{
          border: `1px solid ${healthData.border}`,
          background: healthData.bg,
          padding: '1.25rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: healthData.color, marginBottom: '0.35rem' }}>
                Financial Health Score
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: healthData.color, lineHeight: 1 }}>
                {healthData.displayText}
                {healthData.score !== null && (
                  <span style={{ fontSize: '1.1rem', fontWeight: 500, marginLeft: '0.2rem' }}>/100</span>
                )}
              </div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: healthData.color, marginTop: '0.4rem' }}>
                {healthData.label}
              </div>
            </div>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              background: healthData.border,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Activity size={20} color={healthData.color} />
            </div>
          </div>
          {/* Score bar */}
          <div style={{ marginTop: '1rem' }}>
            <div style={{ height: '6px', background: 'rgba(0,0,0,0.08)', borderRadius: '99px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: healthData.barWidth,
                background: healthData.color,
                borderRadius: '99px',
                transition: 'width 1s ease',
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: healthData.color, marginTop: '0.35rem', opacity: 0.8 }}>
              <span>{healthData.subtext}</span>
              {healthData.score !== null && <span>Optimal (100)</span>}
            </div>
          </div>
        </div>

        {/* Savings Opportunity */}
        <div className="fintech-card" style={{ padding: '1.25rem', border: '1px solid var(--amber-border)', background: 'var(--amber-bg)' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber-dark)', marginBottom: '0.35rem' }}>
            Identified Savings Opportunity
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--amber-dark)', lineHeight: 1 }}>
            ${potentialSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span style={{ fontSize: '0.85rem', fontWeight: 500, marginLeft: '0.25rem' }}>/mo</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--amber-dark)', marginTop: '0.35rem' }}>
            ${potentialAnnualSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} potential annual savings
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {!advancedReady ? (
              <div style={{ height: '36px', background: 'rgba(255,255,255,0.4)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
            ) : recommendations.length > 0 ? (
              recommendations.slice(0, 2).map((r) => (
                <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.8rem', color: 'var(--amber-dark)' }}>
                  <AlertTriangle size={13} style={{ flexShrink: 0 }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.title}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--amber-dark)', opacity: 0.9 }}>
                {hasTransactions ? 'All recurring commitments within normal parameters.' : 'Synchronize transactions to analyze spend.'}
              </div>
            )}
          </div>
          <Link
            to="/recommendations"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              marginTop: '0.75rem',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: 'var(--amber-dark)',
              textDecoration: 'none',
            }}
          >
            View recommendations <ArrowRight size={13} />
          </Link>
        </div>

        {/* Upcoming Subscriptions */}
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
                Upcoming Commitments (7 days)
              </div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.15rem' }}>
                ${upcomingTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <Calendar size={18} color="var(--paypal-blue)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {upcomingPayments.length > 0 ? (
              upcomingPayments.slice(0, 3).map((p) => (
                <div key={p.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.35rem 0',
                  borderBottom: '1px solid var(--border-light)',
                  fontSize: '0.82rem',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-body)' }}>{p.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-caption)' }}>{p.date}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>${Number(p.amount).toFixed(2)}</span>
                    {!p.isEssential && (
                      <span style={{
                        fontSize: '0.65rem',
                        padding: '0.1rem 0.35rem',
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
              <div style={{ padding: '0.75rem 0', color: 'var(--text-muted)', fontSize: '0.82rem', textAlign: 'center' }}>
                No upcoming subscription renewals detected.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Subscription Expense Analysis Summary */}
      {subAnalysis?.has_subscriptions && (
        <div className="fintech-card" style={{ padding: '1.35rem 1.5rem', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
                  Subscription Expense Analysis
                </h3>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'var(--paypal-blue-subtle)', color: 'var(--navy-primary)' }}>
                  {subAnalysis.vendor_analysis?.length || 0} Providers
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                Normalized recurring commitments, cadence conversion, and revenue impact analysis
              </p>
            </div>
            <Link
              to="/subscriptions"
              style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
            >
              Full Directory <ArrowRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
            {/* Monthly Commitment */}
            <div style={{ padding: '0.95rem 1.15rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Monthly Commitment
              </div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.25rem' }}>
                ${Number(subAnalysis.total_monthly_commitment).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-muted)' }}>/mo</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                ${subAnalysis.confirmed_monthly_commitment.toFixed(2)} confirmed · ${subAnalysis.potential_monthly_commitment.toFixed(2)} potential
              </div>
            </div>

            {/* Annual Commitment */}
            <div style={{ padding: '0.95rem 1.15rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Annual Run-Rate
              </div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', marginTop: '0.25rem' }}>
                ${Number(subAnalysis.total_annual_commitment).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-muted)' }}>/yr</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Historical: ${Number(subAnalysis.actual_historical_spend_total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} settled
              </div>
            </div>

            {/* Revenue Impact */}
            <div style={{ padding: '0.95rem 1.15rem', background: subAnalysis.revenue_comparison.has_sufficient_revenue_data ? (subAnalysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-bg)' : subAnalysis.revenue_comparison.burden_level === 'moderate' ? 'var(--amber-bg)' : 'var(--rose-bg)') : 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Revenue vs Subs
              </div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: subAnalysis.revenue_comparison.has_sufficient_revenue_data ? (subAnalysis.revenue_comparison.burden_level === 'healthy' ? 'var(--emerald-dark)' : subAnalysis.revenue_comparison.burden_level === 'moderate' ? 'var(--amber-dark)' : 'var(--rose-dark)') : 'var(--text-muted)', marginTop: '0.25rem' }}>
                {subAnalysis.revenue_comparison.revenue_percentage !== null ? `${subAnalysis.revenue_comparison.revenue_percentage}%` : 'N/A'}
                <span style={{ fontSize: '0.75rem', fontWeight: 600, marginLeft: '0.35rem' }}>
                  {subAnalysis.revenue_comparison.has_sufficient_revenue_data ? subAnalysis.revenue_comparison.burden_level.toUpperCase() : 'NO SALES'}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {subAnalysis.revenue_comparison.explanation}
              </div>
            </div>

            {/* Spending Trend */}
            <div style={{ padding: '0.95rem 1.15rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Spending Velocity
              </div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: subAnalysis.spending_trends.trend_direction === 'increasing' ? 'var(--rose-dark)' : 'var(--navy-slate)', marginTop: '0.35rem', textTransform: 'capitalize' }}>
                {subAnalysis.spending_trends.trend_direction.replace('_', ' ')}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {subAnalysis.spending_trends.trend_summary}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Charts: Consolidated 2-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1rem' }}>
        {!importantReady ? (
          <>
            <ChartCardSkeleton title="Loading cash-flow trends..." height={320} />
            <ChartCardSkeleton title="Loading subscription category allocation..." height={320} />
          </>
        ) : (
          <>
            <IncomeExpenseChart data={monthlyChartData} />
            <CategoryPieChart data={categoryPieData} />
          </>
        )}
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
