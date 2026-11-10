import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import {
  ShieldAlert,
  ShieldCheck,
  Users,
  CreditCard,
  Layers,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [usersList, setUsersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMsg, setActionMsg] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, usersData] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUsers(50),
      ]);
      setStats(statsData);
      setUsersList(usersData);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load admin stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.is_admin) {
      loadData();
    }
  }, [user]);

  const handleRoleToggle = async (userId, currentRole) => {
    try {
      setActionMsg(null);
      await adminAPI.updateUserRole(userId, !currentRole);
      setActionMsg(`User role updated successfully.`);
      // Refresh list
      const updated = await adminAPI.getUsers(50);
      setUsersList(updated);
    } catch (err) {
      setActionMsg(`Error: ${err?.response?.data?.detail || err.message}`);
    }
  };

  if (!user?.is_admin) {
    return (
      <div style={{ maxWidth: '640px', margin: '4rem auto', textAlign: 'center', padding: '2rem' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '16px',
          background: 'rgba(239, 68, 68, 0.1)',
          color: '#ef4444',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.5rem',
        }}>
          <Lock size={32} />
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>
          Admin Privileges Required
        </h2>
        <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
          The operations dashboard is strictly restricted to platform administrators.
          Your current account (<strong>{user?.email}</strong>) does not have administrative rights.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Platform Operations & Metrics</h1>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '99px',
              fontSize: '0.75rem',
              fontWeight: 600,
              background: 'rgba(16, 185, 129, 0.1)',
              color: '#10b981',
            }}>
              <CheckCircle2 size={12} /> {stats?.system_status || 'OPERATIONAL'}
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Real-time multi-tenant platform metrics, PayPal integration health, and user management.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.2rem',
            background: 'var(--bg-card, #fff)',
            border: '1px solid var(--border-light, #e2e8f0)',
            borderRadius: '8px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          Refresh Metrics
        </button>
      </div>

      {actionMsg && (
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          background: 'rgba(14, 165, 233, 0.1)',
          color: '#0284c7',
          marginBottom: '1.5rem',
          fontSize: '0.9rem',
        }}>
          {actionMsg}
        </div>
      )}

      {error && (
        <div style={{
          padding: '1rem',
          borderRadius: '8px',
          background: 'rgba(239, 68, 68, 0.1)',
          color: '#ef4444',
          marginBottom: '1.5rem',
        }}>
          {error}
        </div>
      )}

      {/* KPI Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem',
      }}>
        {/* Total Users */}
        <div style={{
          background: 'var(--bg-card, #fff)',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid var(--border-light, #e2e8f0)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>PLATFORM USERS</span>
            <Users size={18} color="var(--paypal-blue, #0070ba)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            {stats ? stats.total_users : '—'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Individual: {stats?.account_types?.individual || 0} • Household: {stats?.account_types?.household || 0} • Business: {stats?.account_types?.business || 0}
          </div>
        </div>

        {/* Connected PayPal */}
        <div style={{
          background: 'var(--bg-card, #fff)',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid var(--border-light, #e2e8f0)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>CONNECTED PAYPALS</span>
            <CreditCard size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            {stats ? stats.connected_paypals : '—'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Live OAuth & Sandbox connected profiles
          </div>
        </div>

        {/* Total Transactions & Subscriptions */}
        <div style={{
          background: 'var(--bg-card, #fff)',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid var(--border-light, #e2e8f0)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>FINANCIAL LEDGER</span>
            <Layers size={18} color="#8b5cf6" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            {stats ? stats.total_transactions : '—'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Transactions recorded • {stats?.total_subscriptions || 0} Active Subscriptions
          </div>
        </div>

        {/* Webhook Intelligence */}
        <div style={{
          background: 'var(--bg-card, #fff)',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid var(--border-light, #e2e8f0)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>WEBHOOK HEALTH</span>
            <Activity size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            {stats ? `${stats.webhook_health?.verified || 0} / ${stats.webhook_health?.total_received || 0}` : '—'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Verified events • {stats?.webhook_health?.failed_or_rejected || 0} failed/rejected
          </div>
        </div>
      </div>

      {/* Users Management Section */}
      <div style={{
        background: 'var(--bg-card, #fff)',
        borderRadius: '12px',
        padding: '1.5rem',
        border: '1px solid var(--border-light, #e2e8f0)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
      }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem' }}>
          User Directory & Privilege Management
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-light, #e2e8f0)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.75rem 0.5rem' }}>ID</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>User Email</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Full Name</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Account Type</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Company / Entity</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Role</th>
                <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {usersList.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid var(--border-light, #e2e8f0)' }}>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>#{u.id}</td>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 500 }}>{u.email}</td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)' }}>{u.full_name || '—'}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    <span style={{
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      background: 'var(--bg-app, #f8fafc)',
                      textTransform: 'capitalize',
                    }}>
                      {u.account_type}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)' }}>{u.company_name}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    {u.is_admin ? (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        color: '#ef4444',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                      }}>
                        <ShieldAlert size={12} /> Administrator
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>User</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                    {u.id !== user?.id && (
                      <button
                        onClick={() => handleRoleToggle(u.id, u.is_admin)}
                        style={{
                          padding: '0.35rem 0.75rem',
                          borderRadius: '6px',
                          border: '1px solid var(--border-light, #cbd5e1)',
                          background: 'none',
                          cursor: 'pointer',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: u.is_admin ? '#ef4444' : 'var(--paypal-blue, #0070ba)',
                        }}
                      >
                        {u.is_admin ? 'Demote to User' : 'Promote to Admin'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

