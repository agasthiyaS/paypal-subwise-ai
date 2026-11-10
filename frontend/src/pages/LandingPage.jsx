import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  TrendingUp,
  Sliders,
  Sparkles,
  ArrowRight,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Database,
  BarChart3
} from 'lucide-react';

const LandingPage = () => {
  return (
    <div style={{ backgroundColor: '#ffffff', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Banner Notice */}
      <div style={{
        backgroundColor: '#003087',
        color: '#ffffff',
        padding: '0.75rem 1.75rem',
        textAlign: 'center',
        fontSize: '0.95rem',
        fontWeight: 600
      }}>
        FinTech Innovation: Real-time Cash-Flow Stress Testing &amp; SaaS Commitment Optimization
      </div>

      {/* Hero Section */}
      <section style={{
        padding: '5.5rem 2.5rem 4.5rem',
        maxWidth: '1280px',
        margin: '0 auto',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.65rem',
          backgroundColor: '#eff6ff',
          color: '#0070ba',
          padding: '0.55rem 1.25rem',
          borderRadius: '9999px',
          fontSize: '0.92rem',
          fontWeight: 700,
          marginBottom: '2rem',
          border: '1.5px solid #bfdbfe'
        }}>
          <ShieldCheck size={18} /> Intelligent Cash-Flow Affordability Engine
        </div>

        <h1 style={{
          fontSize: '3.25rem',
          fontWeight: 800,
          lineHeight: '1.15',
          letterSpacing: '-0.03em',
          color: 'var(--navy-slate)',
          marginBottom: '1.5rem',
          maxWidth: '900px',
          margin: '0 auto 1.5rem'
        }}>
          Protect Operating Runway from Silent <span style={{ color: 'var(--paypal-blue)' }}>Subscription Creep</span>
        </h1>

        <p style={{
          fontSize: '1.2rem',
          color: 'var(--text-body)',
          maxWidth: '750px',
          margin: '0 auto 2.5rem',
          lineHeight: '1.6'
        }}>
          Small businesses with fluctuating revenue can now evaluate upcoming software commitments before they renew.
          Simulate future cash-flow scenarios, detect creeping licenses, and protect essential operations.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/register" className="btn-fintech btn-fintech-primary btn-lg">
            <span>Get Started Free</span>
            <ArrowRight size={18} />
          </Link>
          <Link to="/login" className="btn-fintech btn-fintech-outline btn-lg">
            <span>Open Demo Workspace</span>
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1.5rem',
          marginTop: '4rem',
          textAlign: 'left'
        }}>
          <div className="fintech-card">
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <TrendingUp size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
              Cash-Flow Forecasting
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Deterministic forward liquidity modeling showing exact depletion horizons and safety thresholds.
            </p>
          </div>

          <div className="fintech-card">
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: '#eff6ff', color: '#0070ba', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Sliders size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
              Scenario Stress Simulator
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Test "What if revenue drops 30%?" or "What if we freeze Tier 3 tools?" with real-time runway impact.
            </p>
          </div>

          <div className="fintech-card">
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: '#fef3c7', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <AlertTriangle size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
              Price Creep Detection
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Automatically detects seat proliferation and unannounced supplier price hikes over consecutive billing cycles.
            </p>
          </div>

          <div className="fintech-card">
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: '#f5f3ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Sparkles size={22} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
              AI Optimization Directives
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Generates quantified consolidation recommendations and pre-drafted supplier contract renegotiation letters.
            </p>
          </div>
        </div>
      </section>

      {/* Problem & Solution Comparison Section */}
      <section style={{ backgroundColor: 'var(--bg-app)', padding: '4rem 2rem', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.75rem' }}>
              The Problem with Standard Payment Statements
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--text-muted)' }}>
              Historical payment ledgers record past disbursements but offer zero foresight into future solvency.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid var(--rose-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-card)'
            }}>
              <div style={{ color: 'var(--rose-dark)', fontWeight: 700, fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={20} /> Traditional Payment Records
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.9rem', color: 'var(--text-body)' }}>
                <li>❌ Shows backward-looking expenses after money has already left.</li>
                <li>❌ Masks redundant tool subscriptions across team silos.</li>
                <li>❌ Blind to upcoming price hikes and automatic renewals.</li>
                <li>❌ Leaves founders guessing how revenue dips affect software affordability.</li>
              </ul>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid var(--emerald-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '2rem',
              boxShadow: 'var(--shadow-card)'
            }}>
              <div style={{ color: 'var(--emerald-dark)', fontWeight: 700, fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={20} /> PayPal SubWise AI
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.9rem', color: 'var(--text-body)' }}>
                <li>✓ Simulates future cash-flow scenarios across baseline, conservative, and stressed states.</li>
                <li>✓ Identifies redundant tools (e.g. Zoom vs Google Meet, Asana vs Notion).</li>
                <li>✓ Classifies subscriptions into Mission-Critical, Important, and Discretionary tiers.</li>
                <li>✓ Calculates exact days of runway extension gained by freezing non-essential software.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        marginTop: 'auto',
        borderTop: '1px solid var(--border-light)',
        padding: '2rem',
        textAlign: 'center',
        fontSize: '0.82rem',
        color: 'var(--text-muted)',
        backgroundColor: '#ffffff'
      }}>
        PayPal SubWise AI — Built for the FinTech Hackathon. Designed for small business financial resilience.
      </footer>
    </div>
  );
};

export default LandingPage;

