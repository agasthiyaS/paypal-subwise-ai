import React, { useState, useEffect } from 'react';
import { simulationAPI } from '../../services/api';
import RunwayChart from '../dashboard/RunwayChart';
import { Sliders, ShieldCheck, AlertTriangle, TrendingUp, DollarSign, Calendar } from 'lucide-react';

const WhatIfSimulator = ({ subscriptions = [], business }) => {
  const [revenueShock, setRevenueShock] = useState(-25);
  const [pauseTier3, setPauseTier3] = useState(true);
  const [selectedPausedIds, setSelectedPausedIds] = useState([]);
  const [additionalBurn, setAdditionalBurn] = useState(0);

  const [simResult, setSimResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSim = async () => {
    setLoading(true);
    try {
      const res = await simulationAPI.runSimulation({
        revenue_shock_pct: Number(revenueShock),
        paused_subscription_ids: selectedPausedIds,
        pause_tier_3_discretionary: pauseTier3,
        additional_monthly_burn: Number(additionalBurn),
      });
      setSimResult(res);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSim();
  }, [revenueShock, pauseTier3, selectedPausedIds, additionalBurn]);

  const toggleSubPause = (id) => {
    setSelectedPausedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Simulation Controls Grid */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
          <Sliders size={20} color="#00cfde" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Interactive Scenario Stress-Test Engine</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {/* Revenue Shock Slider */}
          <div className="slider-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label" style={{ fontWeight: 600 }}>Simulated Revenue Shock</label>
              <span style={{
                fontSize: '0.9rem',
                fontWeight: 700,
                color: revenueShock < 0 ? '#f87171' : revenueShock > 0 ? '#34d399' : 'var(--text-secondary)'
              }}>
                {revenueShock > 0 ? `+${revenueShock}%` : `${revenueShock}%`}
              </span>
            </div>
            <input
              type="range"
              min="-60"
              max="50"
              step="5"
              value={revenueShock}
              onChange={(e) => setRevenueShock(e.target.value)}
              className="slider-track"
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span>-60% (Severe Crunch)</span>
              <span>0% (Baseline)</span>
              <span>+50% (Expansion)</span>
            </div>
          </div>

          {/* Quick Toggles */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', justifyContent: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.88rem' }}>
              <input
                type="checkbox"
                checked={pauseTier3}
                onChange={(e) => setPauseTier3(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: '#0070ba', cursor: 'pointer' }}
              />
              <span style={{ fontWeight: 600 }}>Bulk Freeze Tier 3 (Discretionary) Tools</span>
            </label>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '1.75rem' }}>
              Instantly simulates runway when convenience subscriptions (Dropbox, Mailchimp, Asana) are paused.
            </p>
          </div>

          {/* Custom Burn Adjustment */}
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Custom Monthly Burn Adjustment ($)</label>
            <input
              type="number"
              className="form-input"
              value={additionalBurn}
              onChange={(e) => setAdditionalBurn(e.target.value)}
              placeholder="+/- Monthly Burn (e.g. 2000)"
            />
          </div>
        </div>
      </div>

      {/* Real-Time Impact Metric Cards */}
      {simResult && (
        <div className="stat-grid" style={{ marginBottom: 0 }}>
          <div className="card stat-card">
            <div className="stat-header">
              <span>Simulated Runway</span>
              <Calendar size={18} color="#00cfde" />
            </div>
            <div className="stat-value" style={{ color: simResult.simulated_runway_months < 6 ? '#f87171' : '#34d399' }}>
              {simResult.simulated_runway_months >= 90 ? '24+ Mo' : `${simResult.simulated_runway_months} Mo`}
            </div>
            <div className="stat-footer">
              <span>Depletion Horizon: <strong>{simResult.depletion_status}</strong></span>
            </div>
          </div>

          <div className="card stat-card">
            <div className="stat-header">
              <span>Runway Extension Delta</span>
              <TrendingUp size={18} color="#10b981" />
            </div>
            <div className="stat-value" style={{ color: simResult.runway_delta_months > 0 ? '#34d399' : 'var(--text-primary)' }}>
              {simResult.runway_delta_months > 0 ? `+${simResult.runway_delta_months} Mo` : 'Baseline'}
            </div>
            <div className="stat-footer">
              <span>Additional liquidity extension gained</span>
            </div>
          </div>

          <div className="card stat-card">
            <div className="stat-header">
              <span>Monthly SaaS Capital Saved</span>
              <DollarSign size={18} color="#fbbf24" />
            </div>
            <div className="stat-value" style={{ color: '#fbbf24' }}>
              ${simResult.monthly_savings_from_paused.toFixed(2)}
            </div>
            <div className="stat-footer">
              <span>Annualized preservation: ${(simResult.monthly_savings_from_paused * 12).toLocaleString()}</span>
            </div>
          </div>

          <div className="card stat-card">
            <div className="stat-header">
              <span>Optimized Monthly SaaS Outflow</span>
              <ShieldCheck size={18} color="#60a5fa" />
            </div>
            <div className="stat-value">
              ${simResult.optimized_recurring_subscriptions.toFixed(2)}
            </div>
            <div className="stat-footer">
              <span>Down from ${simResult.monthly_recurring_subscriptions.toFixed(2)}/mo</span>
            </div>
          </div>
        </div>
      )}

      {/* Projection Chart */}
      {simResult && (
        <RunwayChart
          timeline={simResult.timeline}
          title={`Stress Simulation Result (${revenueShock >= 0 ? '+' : ''}${revenueShock}% Revenue Shock)`}
        />
      )}

      {/* Granular Selective Tool Pausing */}
      <div className="card">
        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.85rem' }}>
          Selectively Toggle Specific Subscriptions for Affordability Modeling:
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
          {subscriptions.map((s) => {
            const isPausedExplicitly = selectedPausedIds.includes(s.id);
            const isTier3Bulk = pauseTier3 && s.priority_tier === 3;
            const activePause = isPausedExplicitly || isTier3Bulk;

            return (
              <div
                key={s.id}
                onClick={() => toggleSubPause(s.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background: activePause ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-tertiary)',
                  border: `1px solid ${activePause ? 'rgba(239, 68, 68, 0.3)' : 'var(--border-color)'}`,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, textDecoration: activePause ? 'line-through' : 'none' }}>
                    {s.vendor_name}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    ${s.latest_amount}/mo (Tier {s.priority_tier})
                  </div>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  color: activePause ? '#f87171' : '#34d399'
                }}>
                  {activePause ? 'PAUSED' : 'ACTIVE'}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WhatIfSimulator;

