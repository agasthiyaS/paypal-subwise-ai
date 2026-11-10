import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { savingsAPI } from '../services/api';
import {
  Sparkles,
  Search,
  TrendingDown,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  BookOpen,
  Layers,
  DollarSign,
  Star,
  Tag,
  Filter,
} from 'lucide-react';

// ─── Helpers ─────────────────────────────────────────────────────────────────
const fmt = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const confidenceColor = (level) => {
  if (level === 'high') return { bg: '#ecfdf5', color: '#059669', border: '#a7f3d0' };
  if (level === 'medium') return { bg: '#fef3c7', color: '#d97706', border: '#fde68a' };
  return { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' };
};

// ─── Opportunity Card ─────────────────────────────────────────────────────────
const OpportunityCard = ({ item }) => {
  const alt = item.recommended_alternative || {};
  const currentService = item.current_service_name || item.current_service || 'Current Service';
  const altName = alt.name || item.alternative_name || 'Economical Alternative';
  const monthlySavings = alt.estimated_monthly_savings ?? item.monthly_savings ?? 0;
  const annualSavings = alt.estimated_annual_savings ?? item.annual_savings ?? (monthlySavings * 12);
  const currentPrice = item.current_monthly_cost ?? item.current_price ?? item.current_price_monthly ?? 0;
  const altPrice = alt.monthly_equivalent ?? alt.price ?? item.alternative_price_monthly ?? 0;
  const features = alt.features || item.key_features || [];
  const tradeOffs = alt.trade_offs || item.trade_offs || [];
  const confidence = item.confidence || item.confidence_level || 'medium';
  const conf = confidenceColor(confidence.toLowerCase());

  return (
    <div style={{
      background: '#fff',
      border: '1.5px solid #e2e8f0',
      borderRadius: '12px',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      boxShadow: '0 1px 6px rgba(0,0,0,0.05)',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.3rem' }}>
            {item.category}
          </div>
          <div style={{ fontWeight: 800, fontSize: '1rem', color: '#0f172a', lineHeight: 1.3, marginBottom: '0.25rem' }}>
            {currentService} → {altName}
          </div>
          <div style={{ fontSize: '0.82rem', color: '#475569' }}>
            {item.summary_verdict || item.alternative_description || alt.tier || ''}
          </div>
        </div>

        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: '0.2rem' }}>Monthly Savings</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#059669', lineHeight: 1 }}>
            {fmt(monthlySavings)}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#16a34a', fontWeight: 600 }}>
            {fmt(annualSavings)}/yr
          </div>
        </div>
      </div>

      {/* Pricing comparison */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '120px', background: '#fee2e2', borderRadius: '8px', padding: '0.65rem 0.85rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#b91c1c', marginBottom: '0.1rem' }}>CURRENT</div>
          <div style={{ fontWeight: 800, color: '#7f1d1d', fontSize: '1.05rem' }}>{fmt(currentPrice)}/mo</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', color: '#94a3b8' }}>
          <ArrowRight size={16} />
        </div>
        <div style={{ flex: 1, minWidth: '120px', background: '#dcfce7', borderRadius: '8px', padding: '0.65rem 0.85rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#15803d', marginBottom: '0.1rem' }}>ALTERNATIVE</div>
          <div style={{ fontWeight: 800, color: '#14532d', fontSize: '1.05rem' }}>{fmt(altPrice)}/mo</div>
        </div>
      </div>

      {/* Features vs Trade-offs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        {features.length > 0 && (
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#059669', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <CheckCircle2 size={12} /> Features
            </div>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              {features.slice(0, 3).map((f, i) => (
                <li key={i} style={{ fontSize: '0.78rem', color: '#374151', display: 'flex', alignItems: 'flex-start', gap: '0.3rem' }}>
                  <span style={{ color: '#059669', marginTop: '1px' }}>✓</span> {f}
                </li>
              ))}
            </ul>
          </div>
        )}
        {tradeOffs.length > 0 && (
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#d97706', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <AlertCircle size={12} /> Trade-offs
            </div>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              {tradeOffs.slice(0, 3).map((t, i) => (
                <li key={i} style={{ fontSize: '0.78rem', color: '#374151', display: 'flex', alignItems: 'flex-start', gap: '0.3rem' }}>
                  <span style={{ color: '#d97706', marginTop: '1px' }}>⚠</span> {t}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Footer: confidence badge + source note */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid #f1f5f9' }}>
        <span style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '0.2rem 0.6rem',
          borderRadius: '99px',
          background: conf.bg,
          color: conf.color,
          border: `1px solid ${conf.border}`,
        }}>
          {confidence.toUpperCase()} CONFIDENCE
        </span>
        {(alt.source || item.source_note) && (
          <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontStyle: 'italic' }}>
            {alt.source ? `Source: ${alt.source} (${alt.source_date || '2026'})` : item.source_note}
          </span>
        )}
      </div>
    </div>
  );
};

// ─── Catalog Item Row ─────────────────────────────────────────────────────────
const CatalogRow = ({ item }) => {
  const alt = item.recommended_alternative || {};
  const currentService = item.current_service_name || item.current_service || 'Service';
  const altName = alt.name || item.alternative_name || 'Alternative';
  const monthlySavings = alt.estimated_monthly_savings ?? item.monthly_savings ?? 0;
  const annualSavings = alt.estimated_annual_savings ?? item.annual_savings ?? (monthlySavings * 12);
  const confidence = item.confidence || item.confidence_level || 'medium';
  const conf = confidenceColor(confidence.toLowerCase());

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      padding: '1rem 1.25rem',
      background: '#fff',
      border: '1px solid #e2e8f0',
      borderRadius: '10px',
      flexWrap: 'wrap',
    }}>
      <div style={{ flex: 1, minWidth: '180px' }}>
        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: '0.1rem' }}>{item.category}</div>
        <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#0f172a' }}>
          {currentService} → {altName}
        </div>
        <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.1rem' }}>
          {item.summary_verdict || alt.tier || ''}
        </div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontWeight: 800, color: '#059669', fontSize: '1rem' }}>Save {fmt(monthlySavings)}/mo</div>
        <div style={{ fontSize: '0.75rem', color: '#16a34a' }}>{fmt(annualSavings)}/yr</div>
      </div>
      <span style={{
        fontSize: '0.7rem',
        fontWeight: 700,
        padding: '0.2rem 0.5rem',
        borderRadius: '99px',
        background: conf.bg,
        color: conf.color,
        border: `1px solid ${conf.border}`,
        flexShrink: 0,
      }}>
        {confidence.toUpperCase()}
      </span>
    </div>
  );
};

// ─── Empty State ──────────────────────────────────────────────────────────────
const EmptyState = ({ message }) => (
  <div style={{
    textAlign: 'center',
    padding: '3rem 2rem',
    color: '#64748b',
  }}>
    <Sparkles size={36} color="#cbd5e1" strokeWidth={1.5} style={{ marginBottom: '0.75rem' }} />
    <div style={{ fontWeight: 700, fontSize: '1rem', color: '#475569', marginBottom: '0.4rem' }}>No results found</div>
    <div style={{ fontSize: '0.88rem' }}>{message}</div>
  </div>
);

// ─── Tab Button ───────────────────────────────────────────────────────────────
const TabBtn = ({ label, icon: Icon, active, onClick, badge }) => (
  <button
    onClick={onClick}
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.4rem',
      padding: '0.55rem 1.1rem',
      borderRadius: '8px',
      border: active ? '1.5px solid #0070ba' : '1.5px solid #e2e8f0',
      background: active ? '#eff6ff' : '#fff',
      color: active ? '#0070ba' : '#475569',
      fontWeight: 700,
      fontSize: '0.87rem',
      cursor: 'pointer',
      transition: 'all 0.15s ease',
    }}
  >
    <Icon size={15} />
    {label}
    {badge && (
      <span style={{
        marginLeft: '0.3rem',
        fontSize: '0.68rem',
        fontWeight: 700,
        padding: '0.1rem 0.4rem',
        background: active ? '#0070ba' : '#e2e8f0',
        color: active ? '#fff' : '#64748b',
        borderRadius: '99px',
      }}>{badge}</span>
    )}
  </button>
);

// ─── Main Page ────────────────────────────────────────────────────────────────
const SavingsDiscoveryPage = () => {
  const [tab, setTab] = useState('personalized');
  const [opportunities, setOpportunities] = useState(null);
  const [catalog, setCatalog] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load personalized opportunities on mount
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await savingsAPI.getOpportunities();
        setOpportunities(data);
      } catch (err) {
        setError('Unable to load savings opportunities. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Load catalog when tab switches to catalog
  useEffect(() => {
    if (tab !== 'catalog') return;
    if (catalog.length > 0) return;
    const load = async () => {
      setCatalogLoading(true);
      try {
        const data = await savingsAPI.getCatalog();
        setCatalog(data || []);
      } catch (err) {
        console.error('Catalog load error:', err);
      } finally {
        setCatalogLoading(false);
      }
    };
    load();
  }, [tab]);

  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (q.length < 2) return;
    setSearching(true);
    try {
      const data = await savingsAPI.search(q);
      setSearchResults(data || []);
    } catch (err) {
      console.error('Search error:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, [searchQuery]);

  const handleSearchKey = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  const totalMonthlySavings = opportunities?.total_identified_monthly_savings ?? opportunities?.total_monthly_savings ?? 0;
  const totalAnnualSavings = opportunities?.total_identified_annual_savings ?? opportunities?.total_annual_savings ?? 0;
  const rankedOps = opportunities?.ranked_opportunities || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
            background: '#ecfdf5', color: '#059669', padding: '0.3rem 0.8rem',
            borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.5rem',
          }}>
            <Sparkles size={13} /> Smart Savings Discovery
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.3rem', lineHeight: 1.25 }}>
            Savings Opportunities
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
            Economical alternatives to your recurring services, ranked by verified monthly savings potential
          </p>
        </div>

        {/* Summary badges */}
        {opportunities && (
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ background: '#ecfdf5', border: '1.5px solid #a7f3d0', borderRadius: '12px', padding: '0.85rem 1.25rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#15803d', marginBottom: '0.15rem', textTransform: 'uppercase' }}>Monthly Potential</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#059669', lineHeight: 1 }}>{fmt(totalMonthlySavings)}</div>
            </div>
            <div style={{ background: '#eff6ff', border: '1.5px solid #bfdbfe', borderRadius: '12px', padding: '0.85rem 1.25rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#1d4ed8', marginBottom: '0.15rem', textTransform: 'uppercase' }}>Annual Potential</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#1d4ed8', lineHeight: 1 }}>{fmt(totalAnnualSavings)}</div>
            </div>
          </div>
        )}
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        <TabBtn
          label="Personalized"
          icon={Star}
          active={tab === 'personalized'}
          onClick={() => setTab('personalized')}
          badge={rankedOps.length > 0 ? rankedOps.length : undefined}
        />
        <TabBtn
          label="Full Catalog"
          icon={BookOpen}
          active={tab === 'catalog'}
          onClick={() => setTab('catalog')}
        />
        <TabBtn
          label="Search Alternatives"
          icon={Search}
          active={tab === 'search'}
          onClick={() => setTab('search')}
        />
      </div>

      {/* ── Tab Content ───────────────────────────────────────────────────── */}

      {/* PERSONALIZED TAB */}
      {tab === 'personalized' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
              <RefreshCw size={28} className="spin-icon" color="#0070ba" style={{ marginBottom: '0.75rem' }} />
              <div>Loading personalized opportunities...</div>
            </div>
          ) : error ? (
            <div style={{ padding: '1.5rem', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '10px', color: '#b91c1c', fontSize: '0.9rem' }}>
              {error}
            </div>
          ) : rankedOps.length > 0 ? (
            rankedOps.map((item, idx) => <OpportunityCard key={idx} item={item} />)
          ) : (
            <EmptyState message="Connect PayPal or add subscriptions from the Subscriptions page to see personalized savings recommendations." />
          )}

          {/* Disclaimer */}
          <div style={{
            padding: '1rem 1.25rem',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            fontSize: '0.78rem',
            color: '#64748b',
            lineHeight: 1.55,
          }}>
            <strong>Disclaimer:</strong> Pricing data sourced from published vendor websites (Q4 2026). Actual prices may vary by region, promotional availability, or plan tier.
            All savings estimates are projections based on verified catalog data — not guarantees. Switching decisions remain entirely at your discretion. SubWise AI does not
            receive referral fees from any recommended vendor.
          </div>
        </div>
      )}

      {/* CATALOG TAB */}
      {tab === 'catalog' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600, marginBottom: '0.25rem' }}>
            Verified market catalog — Q4 2026 · Pricing sourced from public vendor pages
          </div>
          {catalogLoading ? (
            <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
              <RefreshCw size={24} className="spin-icon" color="#0070ba" />
              <div style={{ marginTop: '0.75rem' }}>Loading catalog...</div>
            </div>
          ) : catalog.length > 0 ? (
            catalog.map((item, idx) => <CatalogRow key={idx} item={item} />)
          ) : (
            <EmptyState message="Catalog data is currently unavailable. Please try again later." />
          )}
        </div>
      )}

      {/* SEARCH TAB */}
      {tab === 'search' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Search bar */}
          <div style={{ display: 'flex', gap: '0.65rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKey}
                placeholder="Search: streaming, storage, broadband, mobile..."
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem 0.75rem 2.5rem',
                  border: '1.5px solid #e2e8f0',
                  borderRadius: '10px',
                  fontSize: '0.9rem',
                  color: '#0f172a',
                  background: '#fff',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={searching || searchQuery.trim().length < 2}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#0070ba',
                color: '#fff',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: searching ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                opacity: searching || searchQuery.trim().length < 2 ? 0.6 : 1,
              }}
            >
              {searching ? <RefreshCw size={15} className="spin-icon" /> : <Search size={15} />}
              Search
            </button>
          </div>

          {/* Quick suggestions */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {['streaming', 'storage', 'broadband', 'mobile', 'productivity'].map((kw) => (
              <button
                key={kw}
                onClick={() => { setSearchQuery(kw); }}
                style={{
                  padding: '0.3rem 0.8rem',
                  background: '#f1f5f9',
                  border: '1px solid #e2e8f0',
                  borderRadius: '99px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: '#475569',
                  cursor: 'pointer',
                }}
              >
                {kw}
              </button>
            ))}
          </div>

          {/* Results */}
          {searchResults.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 600 }}>
                {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
              </div>
              {searchResults.map((item, idx) => <CatalogRow key={idx} item={item} />)}
            </div>
          ) : searchQuery && !searching ? (
            <EmptyState message={`No alternatives found for "${searchQuery}". Try a broader keyword like "streaming" or "storage".`} />
          ) : null}
        </div>
      )}
    </div>
  );
};

export default SavingsDiscoveryPage;

