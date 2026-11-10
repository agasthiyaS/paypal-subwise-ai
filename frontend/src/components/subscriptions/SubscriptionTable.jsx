import React, { useState } from 'react';
import { subscriptionsAPI } from '../../services/api';
import { AlertCircle, CheckCircle, PauseCircle, PlayCircle, Flame, Shield, ArrowUpRight } from 'lucide-react';

const SubscriptionTable = ({ subscriptions = [], onUpdated }) => {
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [filterTier, setFilterTier] = useState('ALL');
  const [updatingId, setUpdatingId] = useState(null);

  const categories = ['ALL', ...new Set(subscriptions.map((s) => s.category))];

  const handleTierChange = async (subId, newTier) => {
    setUpdatingId(subId);
    try {
      await subscriptionsAPI.updateSubscription(subId, { priority_tier: Number(newTier) });
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Failed to update priority tier');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleStatusToggle = async (sub) => {
    setUpdatingId(sub.id);
    const newStatus = sub.status === 'paused' ? 'active' : 'paused';
    try {
      await subscriptionsAPI.updateSubscription(sub.id, { status: newStatus });
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Failed to update status');
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = subscriptions.filter((s) => {
    const matchSearch = s.vendor_name.toLowerCase().includes(search.toLowerCase()) ||
                        s.category.toLowerCase().includes(search.toLowerCase());
    const matchCat = filterCategory === 'ALL' || s.category === filterCategory;
    const matchTier = filterTier === 'ALL' || String(s.priority_tier) === filterTier;
    return matchSearch && matchCat && matchTier;
  });

  return (
    <div className="card" style={{ padding: '2rem' }}>
      {/* Search & Filter Controls */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
        <input
          type="text"
          className="form-input"
          placeholder="Search SaaS vendor or category..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '320px', minHeight: '50px' }}
        />

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <select
            className="form-input"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            style={{ padding: '0.65rem 1rem', minHeight: '50px', width: 'auto' }}
          >
            {categories.map((c) => (
              <option key={c} value={c}>Category: {c}</option>
            ))}
          </select>

          <select
            className="form-input"
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            style={{ padding: '0.65rem 1rem', minHeight: '50px', width: 'auto' }}
          >
            <option value="ALL">All Tiers</option>
            <option value="1">Tier 1: Mission Critical</option>
            <option value="2">Tier 2: Important</option>
            <option value="3">Tier 3: Discretionary</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Vendor / Tool</th>
              <th>Category</th>
              <th>Billing Cadence</th>
              <th>Cost (Monthly)</th>
              <th>Priority Tier</th>
              <th>Detection Alert</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No subscriptions match the criteria.
                </td>
              </tr>
            ) : (
              filtered.map((sub) => {
                const isZombie = sub.status === 'zombie';
                const hasPriceCreep = (sub.price_change_pct || 0) >= 15;
                const isPaused = sub.status === 'paused';

                return (
                  <tr key={sub.id} style={{ opacity: isPaused ? 0.6 : 1 }}>
                    <td style={{ fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        <span>{sub.vendor_name}</span>
                        {sub.detection_type === 'potential' && (
                          <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a' }}>
                            Potential
                          </span>
                        )}
                        {sub.billing_type === 'variable' && (
                          <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                            Variable
                          </span>
                        )}
                        {sub.confidence_score >= 0.9 && (
                          <span title="High Confidence Detection" style={{ color: '#10b981' }}>
                            <CheckCircle size={14} />
                          </span>
                        )}
                      </div>
                      {sub.detection_reason && (
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 400, marginTop: '0.15rem', fontStyle: 'italic', maxWidth: '280px', lineHeight: 1.3 }}>
                          {sub.detection_reason}
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-body)', fontSize: '0.95rem' }}>{sub.category}</td>
                    <td>
                      <span style={{ textTransform: 'capitalize', fontSize: '0.92rem', fontWeight: 500 }}>{sub.cadence}</span>
                    </td>
                    <td style={{ fontWeight: 700, color: 'var(--navy-slate)', fontSize: '0.98rem', fontFamily: 'JetBrains Mono, monospace' }}>
                      ${sub.latest_amount.toFixed(2)}
                      {sub.cadence === 'annual' && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                          (${(sub.latest_amount / 12).toFixed(2)}/mo)
                        </div>
                      )}
                    </td>
                    <td>
                      <select
                        value={sub.priority_tier}
                        disabled={updatingId === sub.id}
                        onChange={(e) => handleTierChange(sub.id, e.target.value)}
                        className="form-input"
                        style={{
                          padding: '0.35rem 0.65rem',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          background: sub.priority_tier === 1 ? 'rgba(59, 130, 246, 0.15)' : sub.priority_tier === 2 ? 'rgba(168, 85, 247, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                          color: sub.priority_tier === 1 ? '#2563eb' : sub.priority_tier === 2 ? '#9333ea' : '#e11d48',
                          border: 'none',
                          cursor: 'pointer'
                        }}
                      >
                        <option value="1">Tier 1: Core</option>
                        <option value="2">Tier 2: Important</option>
                        <option value="3">Tier 3: Discretionary</option>
                      </select>
                    </td>
                    <td>
                      {isZombie ? (
                        <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#dc2626', border: '1px solid rgba(239, 68, 68, 0.3)', fontSize: '0.82rem' }}>
                          <Flame size={13} /> Zombie Tool
                        </span>
                      ) : hasPriceCreep ? (
                        <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#d97706', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '0.82rem' }}>
                          <ArrowUpRight size={13} /> +{sub.price_change_pct}% Creep
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Normal</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${isPaused ? 'badge-sandbox' : 'badge-live'}`}>
                        {sub.status}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleStatusToggle(sub)}
                        disabled={updatingId === sub.id}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                      >
                        {isPaused ? (
                          <>
                            <PlayCircle size={14} /> Resume
                          </>
                        ) : (
                          <>
                            <PauseCircle size={14} /> Pause
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SubscriptionTable;

