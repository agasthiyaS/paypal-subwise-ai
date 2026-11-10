import React, { useState, useEffect, useCallback } from 'react';
import { householdAPI, expensesAPI, budgetsAPI } from '../services/api';
import CategoryPieChart from '../components/dashboard/CategoryPieChart';
import {
  Users, UserPlus, Trash2, Edit3, Check, X, RefreshCw, Home,
  DollarSign, TrendingDown, PieChart, ShoppingCart, Zap, AlertTriangle,
  PlusCircle, ShieldCheck, Tag, Sparkles
} from 'lucide-react';

const AVATAR_COLORS = [
  '#0070ba', '#10b981', '#f59e0b', '#8b5cf6',
  '#ef4444', '#ec4899', '#06b6d4', '#6366f1'
];

const CATEGORIES = [
  'Food & Groceries',
  'Electricity & Utilities',
  'Housing & Rent',
  'Shopping',
  'Transportation',
  'Healthcare',
  'Education',
  'Entertainment',
  'Subscriptions',
  'Other',
];

const CATEGORY_COLORS = {
  'Food & Groceries': '#10b981',
  'Electricity & Utilities': '#8b5cf6',
  'Housing & Rent': '#ef4444',
  'Shopping': '#f59e0b',
  'Transportation': '#3b82f6',
  'Healthcare': '#ec4899',
  'Education': '#06b6d4',
  'Entertainment': '#f97316',
  'Subscriptions': '#6366f1',
  'Other': '#94a3b8',
};

const EMPTY_MEMBER = {
  name: '',
  role: 'Member',
  avatar_color: '#0070ba',
  monthly_income_share: '',
};

const EMPTY_EXPENSE = {
  amount: '',
  category: 'Food & Groceries',
  description: '',
  merchant: '',
  expense_date: new Date().toISOString().slice(0, 10),
  payment_method: 'Manual Entry',
  household_member_id: '',
  is_shared: true,
  notes: '',
};

export default function HouseholdPage() {
  const [members, setMembers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'members' | 'expenses' | 'budget'

  // Member form state
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [memberForm, setMemberForm] = useState(EMPTY_MEMBER);
  const [editingMemberId, setEditingMemberId] = useState(null);
  const [submittingMember, setSubmittingMember] = useState(false);

  // Expense form state
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseForm, setExpenseForm] = useState(EMPTY_EXPENSE);
  const [submittingExpense, setSubmittingExpense] = useState(false);

  // Budget form state
  const [budgetAmount, setBudgetAmount] = useState('');
  const [savingBudget, setSavingBudget] = useState(false);
  const [msg, setMsg] = useState(null);

  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [membersData, summaryData, expensesData] = await Promise.all([
        householdAPI.getMembers(),
        householdAPI.getSummary({ month: currentMonth, year: currentYear }),
        expensesAPI.getExpenses({ limit: 100 }),
      ]);
      setMembers(membersData || []);
      setSummary(summaryData || null);
      setExpenses(expensesData || []);
      if (summaryData?.household_budget) {
        setBudgetAmount(String(summaryData.household_budget));
      }
    } catch (err) {
      console.error('HouseholdPage load error:', err);
    } finally {
      setLoading(false);
    }
  }, [currentMonth, currentYear]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Member actions
  const handleSaveMember = async (e) => {
    e.preventDefault();
    if (!memberForm.name.trim()) return;
    setSubmittingMember(true);
    try {
      const payload = {
        name: memberForm.name.trim(),
        role: memberForm.role,
        avatar_color: memberForm.avatar_color,
        monthly_income_share: memberForm.monthly_income_share ? parseFloat(memberForm.monthly_income_share) : 0.0,
      };

      if (editingMemberId) {
        await householdAPI.updateMember(editingMemberId, payload);
      } else {
        await householdAPI.createMember(payload);
      }
      setShowMemberModal(false);
      setMemberForm(EMPTY_MEMBER);
      setEditingMemberId(null);
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save member');
    } finally {
      setSubmittingMember(false);
    }
  };

  const handleDeleteMember = async (id) => {
    if (!window.confirm('Remove this household member? Recorded expenses will be unassigned.')) return;
    try {
      await householdAPI.deleteMember(id);
      await loadData();
    } catch (err) {
      alert('Failed to delete member');
    }
  };

  // Add Household Expense
  const handleSaveExpense = async (e) => {
    e.preventDefault();
    if (!expenseForm.amount || isNaN(parseFloat(expenseForm.amount))) return;
    if (!expenseForm.description.trim()) return;

    setSubmittingExpense(true);
    try {
      const payload = {
        amount: parseFloat(expenseForm.amount),
        expense_type: 'expense',
        category: expenseForm.category,
        description: expenseForm.description.trim(),
        merchant: expenseForm.merchant ? expenseForm.merchant.trim() : null,
        expense_date: expenseForm.expense_date ? new Date(expenseForm.expense_date).toISOString() : new Date().toISOString(),
        payment_method: expenseForm.payment_method,
        household_member_id: expenseForm.household_member_id ? parseInt(expenseForm.household_member_id) : null,
        is_shared: expenseForm.is_shared,
        notes: expenseForm.notes || null,
      };

      await expensesAPI.createExpense(payload);
      setShowExpenseModal(false);
      setExpenseForm(EMPTY_EXPENSE);
      await loadData();
      setMsg({ type: 'success', text: 'Expense recorded successfully!' });
      setTimeout(() => setMsg(null), 4000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record expense');
    } finally {
      setSubmittingExpense(false);
    }
  };

  // Save overall monthly budget
  const handleSaveOverallBudget = async (e) => {
    e.preventDefault();
    if (!budgetAmount || isNaN(parseFloat(budgetAmount))) return;
    setSavingBudget(true);
    try {
      await budgetsAPI.setBudget({
        category: 'Overall',
        amount: parseFloat(budgetAmount),
        period_month: currentMonth,
        period_year: currentYear,
      });
      await loadData();
      setMsg({ type: 'success', text: 'Household budget updated successfully!' });
      setTimeout(() => setMsg(null), 4000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update budget');
    } finally {
      setSavingBudget(false);
    }
  };

  const fmt = (n) => Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const pieData = summary?.category_breakdown?.map(c => ({
    name: c.category,
    value: c.amount,
    color: CATEGORY_COLORS[c.category] || '#94a3b8',
  })) || [];

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', flexDirection: 'column', gap: '1rem' }}>
        <RefreshCw size={28} className="spin-icon" color="var(--paypal-blue)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Loading household finances...</div>
      </div>
    );
  }

  const isUnderBudget = summary ? (summary.household_budget >= summary.total_spent) : true;
  const budgetUtilization = summary?.budget_utilization_percent || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: '#eff6ff', color: '#0070ba', padding: '0.3rem 0.8rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            <Home size={14} /> Shared Household Workspace
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.3rem' }}>
            Household &amp; Family Finances
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Coordinate shared budgets, track groceries and utilities, and manage member expense contributions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              setMemberForm(EMPTY_MEMBER);
              setEditingMemberId(null);
              setShowMemberModal(true);
            }}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ minHeight: '42px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <UserPlus size={16} /> Add Member
          </button>
          <button
            onClick={() => setShowExpenseModal(true)}
            className="btn-fintech btn-fintech-primary"
            style={{ minHeight: '42px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <PlusCircle size={16} /> Record Expense
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {msg && (
        <div style={{
          padding: '0.75rem 1.25rem', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600,
          background: msg.type === 'error' ? '#fee2e2' : '#f0fdf4',
          color: msg.type === 'error' ? '#b91c1c' : '#15803d',
          border: `1px solid ${msg.type === 'error' ? '#fca5a5' : '#86efac'}`,
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          {msg.type === 'error' ? <AlertTriangle size={16} /> : <Check size={16} />}
          {msg.text}
        </div>
      )}

      {/* KPI Cards */}
      <div className="stat-grid">
        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #bfdbfe', background: '#eff6ff' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#1d4ed8', marginBottom: '0.4rem' }}>Monthly Budget</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#1d4ed8' }}>${fmt(summary?.household_budget)}</div>
          <div style={{ fontSize: '0.82rem', color: '#3b82f6', marginTop: '0.25rem' }}>
            {summary ? `$${fmt(summary.budget_remaining)} remaining` : 'Set monthly limit'}
          </div>
        </div>

        <div className="fintech-card" style={{ padding: '1.5rem', border: `1.5px solid ${isUnderBudget ? '#bbf7d0' : '#fca5a5'}`, background: isUnderBudget ? '#f0fdf4' : '#fff1f2' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: isUnderBudget ? '#15803d' : '#dc2626', marginBottom: '0.4rem' }}>Total Spent</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: isUnderBudget ? '#15803d' : '#dc2626' }}>${fmt(summary?.total_spent)}</div>
          <div style={{ fontSize: '0.82rem', color: isUnderBudget ? '#16a34a' : '#ef4444', marginTop: '0.25rem' }}>
            {Math.round(budgetUtilization)}% of budget used
          </div>
        </div>

        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #bbf7d0', background: '#f0fdf4' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#15803d', marginBottom: '0.4rem' }}>Groceries &amp; Food</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#15803d' }}>${fmt(summary?.grocery_spend)}</div>
          <div style={{ fontSize: '0.82rem', color: '#16a34a', marginTop: '0.25rem' }}>Supermarkets &amp; staples</div>
        </div>

        <div className="fintech-card" style={{ padding: '1.5rem', border: '1.5px solid #e9d5ff', background: '#faf5ff' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#7c3aed', marginBottom: '0.4rem' }}>Utilities &amp; Telecom</div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#7c3aed' }}>${fmt(summary?.utility_spend)}</div>
          <div style={{ fontSize: '0.82rem', color: '#8b5cf6', marginTop: '0.25rem' }}>Power, water &amp; fiber</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0', borderBottom: '2px solid #e2e8f0' }}>
        {[
          { key: 'overview', label: 'Household Overview' },
          { key: 'members', label: `Members (${members.length})` },
          { key: 'expenses', label: `Recent Expenses (${expenses.length})` },
          { key: 'budget', label: 'Budget Configuration' },
        ].map(tab => (
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

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Member Spending Breakdown */}
          <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
              Member Spending Attribution
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Track personal vs shared spending breakdown among members
            </p>

            {summary?.member_breakdown && summary.member_breakdown.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                {summary.member_breakdown.map(m => (
                  <div key={m.member_id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <div style={{
                          width: '32px', height: '32px', borderRadius: '50%',
                          background: m.avatar_color || '#0070ba',
                          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 700, fontSize: '0.85rem'
                        }}>
                          {m.member_name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a' }}>{m.member_name}</div>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{m.role || 'Member'}</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.75rem', background: '#eff6ff', color: '#0070ba', padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 700 }}>
                        {Math.round(m.percentage_of_household)}% of total
                      </span>
                    </div>

                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.4rem' }}>
                      ${fmt(m.total_spent)}
                    </div>

                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      {m.expense_count} recorded expenses
                      {m.monthly_income_share > 0 && ` · Pool Contribution: $${fmt(m.monthly_income_share)}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem 0', color: '#94a3b8' }}>
                <Users size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
                <div style={{ fontSize: '0.9rem' }}>No member-attributed expenses yet. Add members and assign transactions!</div>
              </div>
            )}
          </div>

          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
            <div className="fintech-card" style={{ padding: '1.75rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Household Category Split</h3>
              {pieData.length > 0 ? (
                <CategoryPieChart data={pieData} />
              ) : (
                <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
                  <PieChart size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
                  <div style={{ fontSize: '0.88rem' }}>No categorized household expenses recorded this month.</div>
                </div>
              )}
            </div>

            <div className="fintech-card" style={{ padding: '1.75rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>Shared vs Personal Ratio</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{ background: '#f8fafc', padding: '1.25rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Shared Living Pool</span>
                    <span style={{ fontWeight: 800, fontSize: '1rem', color: '#0070ba' }}>${fmt(summary?.shared_spend)}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Groceries, rent, home utilities &amp; family streaming</div>
                </div>

                <div style={{ background: '#f8fafc', padding: '1.25rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>Personal Discretionary</span>
                    <span style={{ fontWeight: 800, fontSize: '1rem', color: '#f59e0b' }}>${fmt(summary?.personal_spend)}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Individual dining, entertainment &amp; shopping</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: MEMBERS */}
      {activeTab === 'members' && (
        <div className="fintech-card" style={{ padding: '1.75rem 2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
                Household Member Profiles
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Manage family or housemate roster for expense attribution
              </p>
            </div>
            <button
              onClick={() => {
                setMemberForm(EMPTY_MEMBER);
                setEditingMemberId(null);
                setShowMemberModal(true);
              }}
              className="btn-fintech btn-fintech-primary btn-sm"
              style={{ minHeight: '40px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <UserPlus size={15} /> Add Member
            </button>
          </div>

          {members.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
              <Users size={36} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
              <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem' }}>No household members yet</div>
              <div style={{ fontSize: '0.85rem' }}>Add yourself and other family members to start attributing expenses.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              {members.map(m => (
                <div key={m.id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: '40px', height: '40px', borderRadius: '50%',
                          background: m.avatar_color || '#0070ba',
                          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 800, fontSize: '1.1rem'
                        }}>
                          {m.name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: '1rem', color: '#0f172a' }}>{m.name}</div>
                          <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{m.role || 'Member'}</div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '0.3rem' }}>
                        <button
                          onClick={() => {
                            setMemberForm({
                              name: m.name,
                              role: m.role || 'Member',
                              avatar_color: m.avatar_color || '#0070ba',
                              monthly_income_share: m.monthly_income_share ? String(m.monthly_income_share) : '',
                            });
                            setEditingMemberId(m.id);
                            setShowMemberModal(true);
                          }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', padding: '0.3rem' }}
                          title="Edit member"
                        >
                          <Edit3 size={15} />
                        </button>
                        <button
                          onClick={() => handleDeleteMember(m.id)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: '0.3rem' }}
                          title="Remove member"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', background: '#fff', padding: '0.6rem 0.8rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginTop: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Monthly Pool Allocation:</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>
                        {m.monthly_income_share > 0 ? `$${fmt(m.monthly_income_share)}` : 'Flexible'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: RECENT EXPENSES */}
      {activeTab === 'expenses' && (
        <div className="fintech-card" style={{ padding: '1.5rem 2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
              Recent Household Expenses
            </h3>
            <button
              onClick={() => setShowExpenseModal(true)}
              className="btn-fintech btn-fintech-primary btn-sm"
              style={{ minHeight: '38px', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <PlusCircle size={15} /> Add Expense
            </button>
          </div>

          {expenses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
              <ShoppingCart size={36} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
              <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem' }}>No expenses recorded yet</div>
              <div style={{ fontSize: '0.85rem' }}>Use "Record Expense" to add grocery bills, utilities, or shared expenses.</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                    {['Date', 'Description', 'Category', 'Member', 'Pool', 'Amount'].map(h => (
                      <th key={h} style={{ padding: '0.65rem 0.75rem', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {expenses.map(exp => (
                    <tr key={exp.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.75rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                        {exp.expense_date ? new Date(exp.expense_date).toLocaleDateString() : '—'}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ fontWeight: 600, color: '#0f172a' }}>{exp.description}</div>
                        {exp.merchant && <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{exp.merchant}</div>}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{ fontSize: '0.78rem', fontWeight: 600, padding: '0.2rem 0.5rem', borderRadius: '4px', background: '#f8fafc', border: '1px solid #e2e8f0', color: '#475569' }}>
                          {exp.category}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', color: '#0f172a', fontWeight: 600 }}>
                        {exp.member_name || <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Unassigned</span>}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px',
                          background: exp.is_shared ? '#eff6ff' : '#fef3c7',
                          color: exp.is_shared ? '#0070ba' : '#b45309'
                        }}>
                          {exp.is_shared ? 'Shared' : 'Personal'}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', fontWeight: 700, color: '#dc2626', whiteSpace: 'nowrap' }}>
                        -${Number(exp.amount).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: BUDGET SETTINGS */}
      {activeTab === 'budget' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
          <div className="fintech-card" style={{ padding: '1.75rem', border: '1.5px solid #bfdbfe', background: '#eff6ff' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
              Household Overall Budget
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Set your target monthly shared living spending cap
            </p>

            <form onSubmit={handleSaveOverallBudget}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>
                    Monthly Target (USD)
                  </label>
                  <input
                    type="number" step="1" min="1" required
                    value={budgetAmount}
                    onChange={e => setBudgetAmount(e.target.value)}
                    placeholder="e.g. 3500"
                    style={{ width: '100%', padding: '0.65rem 0.9rem', border: '1px solid #bfdbfe', borderRadius: '8px', fontSize: '0.95rem', boxSizing: 'border-box' }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={savingBudget || !budgetAmount}
                  className="btn-fintech btn-fintech-primary"
                  style={{ minHeight: '42px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                >
                  {savingBudget ? <RefreshCw size={15} className="spin-icon" /> : 'Update Monthly Budget'}
                </button>
              </div>
            </form>
          </div>

          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
              Active Budget Health Check
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Current month pacing against household cap
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                  <span style={{ fontWeight: 600, color: '#475569' }}>Budget Consumed</span>
                  <span style={{ fontWeight: 800, color: '#0f172a' }}>{Math.round(budgetUtilization)}%</span>
                </div>
                <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, Math.round(budgetUtilization))}%`,
                    background: budgetUtilization >= 95 ? '#ef4444' : budgetUtilization >= 75 ? '#f59e0b' : '#10b981',
                    borderRadius: '99px',
                    transition: 'width 0.4s'
                  }} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Remaining Balance:</span>
                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: isUnderBudget ? '#15803d' : '#dc2626' }}>
                  ${fmt(summary?.budget_remaining)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: ADD/EDIT MEMBER */}
      {showMemberModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999, padding: '1rem'
        }}>
          <div style={{ background: '#fff', borderRadius: '14px', width: '100%', maxWidth: '440px', padding: '1.75rem', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
                {editingMemberId ? 'Edit Household Member' : 'Add Household Member'}
              </h3>
              <button onClick={() => setShowMemberModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveMember}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Name *</label>
                  <input
                    type="text" required
                    value={memberForm.name}
                    onChange={e => setMemberForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g. Sarah Connor"
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Role</label>
                  <select
                    value={memberForm.role}
                    onChange={e => setMemberForm(p => ({ ...p, role: e.target.value }))}
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                  >
                    <option value="Primary / Organizer">Primary / Organizer</option>
                    <option value="Partner / Spouse">Partner / Spouse</option>
                    <option value="Family Member">Family Member</option>
                    <option value="Housemate">Housemate</option>
                    <option value="Dependent">Dependent</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Color Badge</label>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {AVATAR_COLORS.map(c => (
                      <button
                        type="button" key={c}
                        onClick={() => setMemberForm(p => ({ ...p, avatar_color: c }))}
                        style={{
                          width: '28px', height: '28px', borderRadius: '50%', background: c, border: memberForm.avatar_color === c ? '3px solid #0f172a' : '2px solid transparent',
                          cursor: 'pointer'
                        }}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Monthly Household Pool Contribution (USD)</label>
                  <input
                    type="number" step="1" min="0"
                    value={memberForm.monthly_income_share}
                    onChange={e => setMemberForm(p => ({ ...p, monthly_income_share: e.target.value }))}
                    placeholder="Voluntary monthly pool allocation"
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                  <button type="button" onClick={() => setShowMemberModal(false)} className="btn-fintech btn-fintech-outline btn-sm">
                    Cancel
                  </button>
                  <button type="submit" disabled={submittingMember} className="btn-fintech btn-fintech-primary btn-sm">
                    {submittingMember ? <RefreshCw size={14} className="spin-icon" /> : (editingMemberId ? 'Save Changes' : 'Create Member')}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: RECORD HOUSEHOLD EXPENSE */}
      {showExpenseModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999, padding: '1rem'
        }}>
          <div style={{ background: '#fff', borderRadius: '14px', width: '100%', maxWidth: '500px', padding: '1.75rem', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0 }}>
                Record Household Expense
              </h3>
              <button onClick={() => setShowExpenseModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveExpense}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Amount (USD) *</label>
                  <input
                    type="number" step="0.01" min="0.01" required
                    value={expenseForm.amount}
                    onChange={e => setExpenseForm(p => ({ ...p, amount: e.target.value }))}
                    placeholder="0.00"
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Category</label>
                  <select
                    value={expenseForm.category}
                    onChange={e => setExpenseForm(p => ({ ...p, category: e.target.value }))}
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                  >
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Description *</label>
                  <input
                    type="text" required
                    value={expenseForm.description}
                    onChange={e => setExpenseForm(p => ({ ...p, description: e.target.value }))}
                    placeholder="e.g. Weekly grocery stock up at Trader Joe's"
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Attributed Member</label>
                  <select
                    value={expenseForm.household_member_id}
                    onChange={e => setExpenseForm(p => ({ ...p, household_member_id: e.target.value }))}
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', background: '#fff' }}
                  >
                    <option value="">Unassigned</option>
                    {members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.3rem' }}>Date</label>
                  <input
                    type="date"
                    value={expenseForm.expense_date}
                    onChange={e => setExpenseForm(p => ({ ...p, expense_date: e.target.value }))}
                    style={{ width: '100%', padding: '0.6rem 0.9rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', gridColumn: 'span 2', padding: '0.4rem 0' }}>
                  <input
                    type="checkbox" id="modal_is_shared"
                    checked={expenseForm.is_shared}
                    onChange={e => setExpenseForm(p => ({ ...p, is_shared: e.target.checked }))}
                    style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                  />
                  <label htmlFor="modal_is_shared" style={{ fontSize: '0.88rem', fontWeight: 600, color: '#475569', cursor: 'pointer' }}>
                    Shared household expense (split/pooled cost)
                  </label>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
                <button type="button" onClick={() => setShowExpenseModal(false)} className="btn-fintech btn-fintech-outline btn-sm">
                  Cancel
                </button>
                <button type="submit" disabled={submittingExpense} className="btn-fintech btn-fintech-primary btn-sm">
                  {submittingExpense ? <RefreshCw size={14} className="spin-icon" /> : 'Save Expense'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

