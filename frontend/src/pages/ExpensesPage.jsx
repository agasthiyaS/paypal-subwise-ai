import React, { useState, useEffect, useCallback } from 'react';
import { expensesAPI, budgetsAPI } from '../services/api';
import CategoryPieChart from '../components/dashboard/CategoryPieChart';
import {
  PlusCircle, Trash2, Edit3, Check, X, RefreshCw, TrendingDown,
  TrendingUp, DollarSign, PieChart, Calendar, Tag, Zap, ChevronDown,
  Wallet, AlertTriangle, ShoppingBag, Car, Home, Lightbulb, Heart,
  BookOpen, Tv, Repeat, Package
} from 'lucide-react';

const CATEGORIES = [
  'Food & Groceries',
  'Shopping',
  'Transportation',
  'Electricity & Utilities',
  'Housing & Rent',
  'Healthcare',
  'Education',
  'Entertainment',
  'Subscriptions',
  'Other',
];

const CATEGORY_ICONS = {
  'Food & Groceries': ShoppingBag,
  'Shopping': Package,
  'Transportation': Car,
  'Electricity & Utilities': Lightbulb,
  'Housing & Rent': Home,
  'Healthcare': Heart,
  'Education': BookOpen,
  'Entertainment': Tv,
  'Subscriptions': Repeat,
  'Other': Tag,
};

const CATEGORY_COLORS = {
  'Food & Groceries': '#10b981',
  'Shopping': '#f59e0b',
  'Transportation': '#3b82f6',
  'Electricity & Utilities': '#8b5cf6',
  'Housing & Rent': '#ef4444',
  'Healthcare': '#ec4899',
  'Education': '#06b6d4',
  'Entertainment': '#f97316',
  'Subscriptions': '#6366f1',
  'Other': '#94a3b8',
};

const EMPTY_FORM = {
  amount: '',
  expense_type: 'expense',
  category: 'Other',
  description: '',
  merchant: '',
  expense_date: new Date().toISOString().slice(0, 10),
  is_recurring: false,
  payment_method: 'Manual Entry',
  notes: '',
};

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [filterCategory, setFilterCategory] = useState('All');
  const [filterType, setFilterType] = useState('All');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [activeTab, setActiveTab] = useState('expenses'); // 'expenses' | 'budget'
  const [budgetForm, setBudgetForm] = useState({ category: 'Other', amount: '', period_month: new Date().getMonth() + 1, period_year: new Date().getFullYear() });
  const [savingBudget, setSavingBudget] = useState(false);

  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [expData, sumData, budData] = await Promise.all([
        expensesAPI.getExpenses({ limit: 200 }),
        expensesAPI.getSummary({ month: currentMonth, year: currentYear }),
        budgetsAPI.getBudgets(),
      ]);
      setExpenses(expData || []);
      setSummary(sumData || null);
      setBudgets(budData || []);
    } catch (err) {
      console.error('ExpensesPage load error:', err);
    } finally {
      setLoading(false);
    }
  }, [currentMonth, currentYear]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleSyncPayPal = async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await expensesAPI.syncPayPal();
      setSyncMsg({ type: 'success', text: `Sync complete — ${res.imported || 0} new expenses imported, ${res.skipped || 0} already existed.` });
      await loadAll();
    } catch (err) {
      setSyncMsg({ type: 'error', text: err.response?.data?.detail || 'PayPal sync failed.' });
    } finally {
      setSyncing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (!formData.amount || isNaN(parseFloat(formData.amount)) || parseFloat(formData.amount) <= 0) {
      setFormError('Enter a valid positive amount.');
      return;
    }
    if (!formData.description.trim()) {
      setFormError('Description is required.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount),
        expense_date: formData.expense_date ? new Date(formData.expense_date).toISOString() : new Date().toISOString(),
      };
      if (editingId) {
        await expensesAPI.updateExpense(editingId, payload);
      } else {
        await expensesAPI.createExpense(payload);
      }
      setShowForm(false);
      setFormData(EMPTY_FORM);
      setEditingId(null);
      await loadAll();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save expense.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (exp) => {
    setFormData({
      amount: String(exp.amount),
      expense_type: exp.expense_type || 'expense',
      category: exp.category || 'Other',
      description: exp.description || '',
      merchant: exp.merchant || '',
      expense_date: exp.expense_date ? exp.expense_date.slice(0, 10) : new Date().toISOString().slice(0, 10),
      is_recurring: exp.is_recurring || false,
      payment_method: exp.payment_method || 'Manual Entry',
      notes: exp.notes || '',
    });
    setEditingId(exp.id);
    setShowForm(true);
    setFormError(null);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this expense record?')) return;
    try {
      await expensesAPI.deleteExpense(id);
      await loadAll();
    } catch (err) {
      alert('Failed to delete expense.');
    }
  };

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    if (!budgetForm.amount || isNaN(parseFloat(budgetForm.amount)) || parseFloat(budgetForm.amount) <= 0) return;
    setSavingBudget(true);
    try {
      await budgetsAPI.setBudget({
        category: budgetForm.category,
        amount: parseFloat(budgetForm.amount),
        period_month: budgetForm.period_month,
        period_year: budgetForm.period_year,
      });
      setBudgetForm(prev => ({ ...prev, amount: '' }));
      await loadAll();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save budget.');
    } finally {
      setSavingBudget(false);
    }
  };

  const handleDeleteBudget = async (id) => {
    if (!window.confirm('Remove this budget limit?')) return;
    try {
      await budgetsAPI.deleteBudget(id);
      await loadAll();
    } catch (err) {
      alert('Failed to delete budget.');
    }
  };

  // Filtered list
  const filteredExpenses = expenses.filter(exp => {
    if (filterCategory !== 'All' && exp.category !== filterCategory) return false;
    if (filterType !== 'All' && exp.expense_type !== filterType) return false;
    return true;
  });

  // Build pie chart data from summary
  const pieData = summary?.category_breakdown?.map(c => ({
    name: c.category,
    value: c.amount,
    color: CATEGORY_COLORS[c.category] || '#94a3b8',
  })) || [];

  const fmt = (n) => Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', flexDirection: 'column', gap: '1rem' }}>
        <RefreshCw size={28} className="spin-icon" color="var(--paypal-blue)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Loading expenses...</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: '#eff6ff', color: '#0070ba', padding: '0.3rem 0.8rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            <TrendingDown size={14} /> Personal Expense Tracker
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.3rem' }}>
            Income & Expenses
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Track spending, set budgets, and identify where you can save more.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={handleSyncPayPal}
            disabled={syncing}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ minHeight: '42px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={15} className={syncing ? 'spin-icon' : ''} />
            {syncing ? 'Syncing...' : 'Sync PayPal'}
          </button>
          <button
            onClick={() => { setFormData(EMPTY_FORM); setEditingId(null); setFormError(null); setShowForm(true); }}
            className="btn-fintech btn-fintech-primary"
            style={{ minHeight: '42px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <PlusCircle size={16} /> Add Expense
          </button>
        </div>
      </div>

      {/* Sync Status */}
      {syncMsg && (
        <div style={{
          padding: '0.75rem 1.25rem', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600,
          background: syncMsg.type === 'error' ? '#fee2e2' : '#f0fdf4',
          color: syncMsg.type === 'error' ? '#b91c1c' : '#15803d',
          border: `1px solid ${syncMsg.type === 'error' ? '#fca5a5' : '#86efac'}`,
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          {syncMsg.type === 'error' ? <AlertTriangle size={16} /> : <Check size={16} />}
          {syncMsg.text}
        </div>
      )}

      {/* KPI Cards */}
      <div className="stat-grid">
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #bbf7d0', background: '#f0fdf4' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#15803d', marginBottom: '0.4rem' }}>Total Income</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#15803d' }}>${fmt(summary?.total_income)}</div>
          <div style={{ fontSize: '0.82rem', color: '#16a34a', marginTop: '0.25rem' }}>This month's inflows</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #fca5a5', background: '#fff1f2' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#dc2626', marginBottom: '0.4rem' }}>Total Expenses</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#dc2626' }}>${fmt(summary?.total_expenses)}</div>
          <div style={{ fontSize: '0.82rem', color: '#ef4444', marginTop: '0.25rem' }}>This month's outflows</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #bfdbfe', background: '#eff6ff' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#1d4ed8', marginBottom: '0.4rem' }}>Net Savings</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#1d4ed8' }}>${fmt(summary?.net_savings)}</div>
          <div style={{ fontSize: '0.82rem', color: '#3b82f6', marginTop: '0.25rem' }}>
            {summary?.savings_rate != null ? `${Math.round(summary.savings_rate)}% savings rate` : 'No data yet'}
          </div>
        </div>
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #e9d5ff', background: '#faf5ff' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#7c3aed', marginBottom: '0.4rem' }}>Budget Used</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#7c3aed' }}>
            {summary?.budget_utilization_percent != null ? `${Math.round(summary.budget_utilization_percent)}%` : '—'}
          </div>
          <div style={{ fontSize: '0.82rem', color: '#8b5cf6', marginTop: '0.25rem' }}>
            ${fmt(summary?.budget_remaining)} remaining
          </div>
        </div>
      </div>

      {/* Add/Edit Expense Form */}
      {showForm && (
        <div className="fintech-card" style={{ padding: '1.75rem 2rem', border: '1.5px solid #bfdbfe', background: '#eff6ff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              {editingId ? 'Edit Expense' : 'Add New Entry'}
            </h3>
            <button onClick={() => { setShowForm(false); setEditingId(null); setFormError(null); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              {/* Type */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Type</label>
                <select
                  value={formData.expense_type}
                  onChange={e => setFormData(p => ({ ...p, expense_type: e.target.value }))}
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              {/* Amount */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Amount (USD) *</label>
                <input
                  type="number" step="0.01" min="0.01" required
                  value={formData.amount}
                  onChange={e => setFormData(p => ({ ...p, amount: e.target.value }))}
                  placeholder="0.00"
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                />
              </div>
              {/* Category */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Category</label>
                <select
                  value={formData.category}
                  onChange={e => setFormData(p => ({ ...p, category: e.target.value }))}
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              {/* Date */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Date</label>
                <input
                  type="date"
                  value={formData.expense_date}
                  onChange={e => setFormData(p => ({ ...p, expense_date: e.target.value }))}
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                />
              </div>
              {/* Description */}
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Description *</label>
                <input
                  type="text" required
                  value={formData.description}
                  onChange={e => setFormData(p => ({ ...p, description: e.target.value }))}
                  placeholder="e.g. Supermarket weekly shop"
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                />
              </div>
              {/* Merchant */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Merchant / Payee</label>
                <input
                  type="text"
                  value={formData.merchant}
                  onChange={e => setFormData(p => ({ ...p, merchant: e.target.value }))}
                  placeholder="e.g. Walmart, Netflix"
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                />
              </div>
              {/* Payment Method */}
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Payment Method</label>
                <select
                  value={formData.payment_method}
                  onChange={e => setFormData(p => ({ ...p, payment_method: e.target.value }))}
                  style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                >
                  <option>Manual Entry</option>
                  <option>Cash</option>
                  <option>Debit Card</option>
                  <option>Credit Card</option>
                  <option>PayPal</option>
                  <option>Bank Transfer</option>
                  <option>Other</option>
                </select>
              </div>
              {/* Recurring toggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', paddingTop: '1.4rem' }}>
                <input
                  type="checkbox" id="is_recurring"
                  checked={formData.is_recurring}
                  onChange={e => setFormData(p => ({ ...p, is_recurring: e.target.checked }))}
                  style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                />
                <label htmlFor="is_recurring" style={{ fontSize: '0.88rem', fontWeight: 600, color: '#475569', cursor: 'pointer' }}>
                  Recurring expense
                </label>
              </div>
            </div>

            {formError && (
              <div style={{ padding: '0.65rem 1rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={15} /> {formError}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => { setShowForm(false); setEditingId(null); setFormError(null); }} className="btn-fintech btn-fintech-outline btn-sm" style={{ minHeight: '40px' }}>
                Cancel
              </button>
              <button type="submit" disabled={submitting} className="btn-fintech btn-fintech-primary btn-sm" style={{ minHeight: '40px', minWidth: '120px' }}>
                {submitting ? <RefreshCw size={14} className="spin-icon" /> : (editingId ? 'Save Changes' : 'Add Entry')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tabs: Expenses / Budget */}
      <div style={{ display: 'flex', gap: '0', borderBottom: '2px solid #e2e8f0' }}>
        {[{ key: 'expenses', label: 'Expense List' }, { key: 'analytics', label: 'Analytics' }, { key: 'budget', label: 'Budget Manager' }].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '0.65rem 1.25rem', background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '0.92rem', fontWeight: 700,
              color: activeTab === tab.key ? 'var(--paypal-blue)' : '#64748b',
              borderBottom: `2.5px solid ${activeTab === tab.key ? 'var(--paypal-blue)' : 'transparent'}`,
              marginBottom: '-2px', transition: 'all 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: Expense List */}
      {activeTab === 'expenses' && (
        <div className="fintech-card" style={{ padding: '1.5rem 2rem' }}>
          {/* Filters */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.25rem', alignItems: 'center' }}>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#475569' }}>Filter:</div>
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              style={{ padding: '0.45rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.88rem', background: '#fff' }}
            >
              <option value="All">All Types</option>
              <option value="expense">Expenses Only</option>
              <option value="income">Income Only</option>
            </select>
            <select
              value={filterCategory}
              onChange={e => setFilterCategory(e.target.value)}
              style={{ padding: '0.45rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.88rem', background: '#fff' }}
            >
              <option value="All">All Categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <div style={{ marginLeft: 'auto', fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>
              {filteredExpenses.length} records
            </div>
          </div>

          {/* Expense Table */}
          {filteredExpenses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
              <Wallet size={36} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
              <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem' }}>No expenses yet</div>
              <div style={{ fontSize: '0.85rem' }}>Add an expense above, or sync your PayPal transactions.</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                    {['Date', 'Description', 'Category', 'Method', 'Amount', 'Source', ''].map(h => (
                      <th key={h} style={{ padding: '0.65rem 0.75rem', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredExpenses.map(exp => {
                    const isIncome = exp.expense_type === 'income';
                    const CatIcon = CATEGORY_ICONS[exp.category] || Tag;
                    return (
                      <tr key={exp.id} style={{ borderBottom: '1px solid #f1f5f9', transition: 'background 0.1s' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={{ padding: '0.75rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                          {exp.expense_date ? new Date(exp.expense_date).toLocaleDateString() : '—'}
                        </td>
                        <td style={{ padding: '0.75rem', maxWidth: '240px' }}>
                          <div style={{ fontWeight: 600, color: '#0f172a' }}>{exp.description}</div>
                          {exp.merchant && <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{exp.merchant}</div>}
                          {exp.is_recurring && (
                            <span style={{ fontSize: '0.7rem', background: '#eff6ff', color: '#0070ba', padding: '0.1rem 0.4rem', borderRadius: '4px', fontWeight: 700 }}>Recurring</span>
                          )}
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.25rem 0.6rem' }}>
                            <CatIcon size={12} color={CATEGORY_COLORS[exp.category]} />
                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>{exp.category}</span>
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem', color: '#64748b', fontSize: '0.82rem' }}>
                          {exp.payment_method || '—'}
                        </td>
                        <td style={{ padding: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap', color: isIncome ? '#15803d' : '#dc2626' }}>
                          {isIncome ? '+' : '-'}${Number(exp.amount).toFixed(2)}
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          {(exp.data_source === 'paypal_sync' || exp.data_source === 'paypal') ? (
                            <span style={{ fontSize: '0.72rem', background: '#eff6ff', color: '#0070ba', padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 700, border: '1px solid #bfdbfe' }}>
                              PayPal
                            </span>
                          ) : exp.categorization_method === 'rules_engine' ? (
                            <span style={{ fontSize: '0.72rem', background: '#ecfdf5', color: '#059669', padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 700, border: '1px solid #a7f3d0' }}>
                              Auto-detected
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.72rem', background: '#f8fafc', color: '#64748b', padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 600, border: '1px solid #e2e8f0' }}>
                              Manual
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          {exp.data_source !== 'paypal_sync' && exp.data_source !== 'paypal' ? (
                            <div style={{ display: 'flex', gap: '0.4rem' }}>
                              <button onClick={() => handleEdit(exp)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', padding: '0.25rem' }} title="Edit">
                                <Edit3 size={15} />
                              </button>
                              <button onClick={() => handleDelete(exp.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: '0.25rem' }} title="Delete">
                                <Trash2 size={15} />
                              </button>
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontStyle: 'italic' }}>
                              Synced
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB: Analytics */}
      {activeTab === 'analytics' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {/* Category Breakdown */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Spending by Category</h3>
            {pieData.length > 0 ? (
              <>
                <CategoryPieChart data={pieData} />
                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {summary.category_breakdown.map(c => (
                    <div key={c.category} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: CATEGORY_COLORS[c.category] || '#94a3b8' }} />
                        <span style={{ fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>{c.category}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>{Math.round(c.percentage)}%</span>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>${Number(c.amount).toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
                <PieChart size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
                <div style={{ fontSize: '0.88rem' }}>No expense data for this month yet.</div>
              </div>
            )}
          </div>

          {/* Category Highlights */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Category Highlights</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {[
                { label: 'Groceries', value: summary?.grocery_total, icon: ShoppingBag, color: '#10b981' },
                { label: 'Utilities', value: summary?.utility_total, icon: Lightbulb, color: '#8b5cf6' },
                { label: 'Subscriptions', value: summary?.active_subscriptions_total, icon: Repeat, color: '#6366f1' },
                { label: 'Discretionary', value: summary?.discretionary_total, icon: Tag, color: '#f59e0b' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem 1rem', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: `${item.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <item.icon size={18} color={item.color} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#475569' }}>{item.label}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>${fmt(item.value)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB: Budget Manager */}
      {activeTab === 'budget' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {/* Set Budget Form */}
          <div className="fintech-card" style={{ padding: '1.75rem', border: '1.5px solid #e9d5ff', background: '#faf5ff' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Set Category Budget</h3>
            <form onSubmit={handleSaveBudget}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Category</label>
                  <select
                    value={budgetForm.category}
                    onChange={e => setBudgetForm(p => ({ ...p, category: e.target.value }))}
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #c4b5fd', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                  >
                    <option value="Overall">Overall Monthly Budget</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Monthly Limit (USD)</label>
                  <input
                    type="number" step="1" min="1"
                    value={budgetForm.amount}
                    onChange={e => setBudgetForm(p => ({ ...p, amount: e.target.value }))}
                    placeholder="e.g. 500"
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #c4b5fd', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>
                <button type="submit" disabled={savingBudget || !budgetForm.amount} className="btn-fintech btn-fintech-primary" style={{ minHeight: '42px' }}>
                  {savingBudget ? <RefreshCw size={14} className="spin-icon" /> : 'Save Budget'}
                </button>
              </div>
            </form>
          </div>

          {/* Budget List */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Active Budget Limits</h3>
            {budgets.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 0', color: '#94a3b8' }}>
                <DollarSign size={28} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
                <div style={{ fontSize: '0.88rem' }}>No budget limits set yet.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {budgets.map(b => {
                  const utilPct = b.utilization_percent != null ? Math.min(100, Math.round(b.utilization_percent)) : null;
                  const barColor = utilPct == null ? '#94a3b8' : utilPct >= 90 ? '#ef4444' : utilPct >= 70 ? '#f59e0b' : '#10b981';
                  return (
                    <div key={b.id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '0.9rem 1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>{b.category}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.9rem' }}>${Number(b.amount).toFixed(0)}/mo</span>
                          <button onClick={() => handleDeleteBudget(b.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: '0.2rem' }}>
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>
                      {utilPct != null && (
                        <>
                          <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '99px', overflow: 'hidden', marginBottom: '0.3rem' }}>
                            <div style={{ height: '100%', width: `${utilPct}%`, background: barColor, borderRadius: '99px', transition: 'width 0.4s' }} />
                          </div>
                          <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                            ${Number(b.spent || 0).toFixed(2)} spent · {utilPct}% used
                            {b.remaining != null && ` · $${Number(b.remaining).toFixed(2)} remaining`}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

