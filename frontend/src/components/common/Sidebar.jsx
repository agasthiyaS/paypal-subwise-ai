import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Layers,
  LineChart,
  Sliders,
  Sparkles,
  FileBarChart,
  ShieldCheck,
  TrendingDown,
  MessageSquare,
  Home,
  Activity,
  X
} from 'lucide-react';

const Sidebar = ({ mobileOpen, onClose }) => {
  const { user, business } = useAuth();
  const accountType = business?.account_type || 'business';

  // Build structured navigation groups based on account edition
  const sections = [];

  // 1. OVERVIEW
  sections.push({
    title: 'Overview',
    items: [
      {
        to: '/dashboard',
        label: accountType === 'individual' ? 'Personal Dashboard' : accountType === 'household' ? 'Household Overview' : 'Main Dashboard',
        icon: LayoutDashboard,
      },
    ],
  });

  // 2. HOUSEHOLD WORKSPACE (If Household account)
  if (accountType === 'household') {
    sections.push({
      title: 'Household',
      items: [
        {
          to: '/household',
          label: 'Household Workspace',
          icon: Home,
          badge: 'Family',
          badgeColor: '#0284c7',
          badgeBg: '#f0f9ff',
          badgeBorder: '#bae6fd',
        },
      ],
    });
  }

  // 3. FINANCIAL MANAGEMENT
  if (accountType === 'individual') {
    sections.push({
      title: 'Financial Management',
      items: [
        { to: '/expenses', label: 'Income & Expenses', icon: TrendingDown },
        { to: '/subscriptions', label: 'Subscriptions & Bills', icon: Layers },
      ],
    });
  } else if (accountType === 'household') {
    sections.push({
      title: 'Financial Management',
      items: [
        { to: '/expenses', label: 'Shared Expenses', icon: TrendingDown },
        { to: '/subscriptions', label: 'Shared Subscriptions', icon: Layers },
      ],
    });
  } else {
    // Business
    sections.push({
      title: 'Financial Management',
      items: [
        { to: '/subscriptions', label: 'Subscriptions', icon: Layers },
        { to: '/expenses', label: 'Income & Expenses', icon: TrendingDown },
      ],
    });
  }

  // 4. INTELLIGENCE
  if (accountType === 'individual') {
    sections.push({
      title: 'Intelligence',
      items: [
        {
          to: '/insights',
          label: 'Financial Health',
          icon: Activity,
          badge: 'Score',
          badgeColor: '#16a34a',
          badgeBg: '#f0fdf4',
          badgeBorder: '#bbf7d0',
        },
        {
          to: '/savings-discovery',
          label: 'Savings Discovery',
          icon: Sparkles,
          badge: 'AI',
          badgeColor: '#059669',
          badgeBg: '#ecfdf5',
          badgeBorder: '#a7f3d0',
        },
        { to: '/forecast', label: 'Cash Flow Forecast', icon: LineChart },
        {
          to: '/recommendations',
          label: 'Recommendations',
          icon: Sparkles,
          badge: 'Tailored',
          badgeColor: '#0284c7',
          badgeBg: '#f0f9ff',
          badgeBorder: '#bae6fd',
        },
        { to: '/reports', label: 'Spending Reports', icon: FileBarChart },
      ],
    });
  } else if (accountType === 'household') {
    sections.push({
      title: 'Intelligence',
      items: [
        {
          to: '/insights',
          label: 'Financial Health',
          icon: Activity,
          badge: 'Score',
          badgeColor: '#16a34a',
          badgeBg: '#f0fdf4',
          badgeBorder: '#bbf7d0',
        },
        {
          to: '/savings-discovery',
          label: 'Savings Discovery',
          icon: Sparkles,
          badge: 'AI',
          badgeColor: '#059669',
          badgeBg: '#ecfdf5',
          badgeBorder: '#a7f3d0',
        },
        { to: '/forecast', label: 'Cash Flow Forecast', icon: LineChart },
        {
          to: '/recommendations',
          label: 'Grocery & Deals AI',
          icon: Sparkles,
          badge: 'Deals',
          badgeColor: '#d97706',
          badgeBg: '#fef3c7',
          badgeBorder: '#fde68a',
        },
        { to: '/reports', label: 'Shared Bill Reports', icon: FileBarChart },
      ],
    });
  } else {
    // Business
    sections.push({
      title: 'Intelligence',
      items: [
        { to: '/forecast', label: 'Cash Flow Forecast', icon: LineChart },
        { to: '/simulator', label: 'Scenario Simulator', icon: Sliders },
        {
          to: '/recommendations',
          label: 'Recommendations',
          icon: Sparkles,
          badge: 'AI',
          badgeColor: '#059669',
          badgeBg: '#ecfdf5',
          badgeBorder: '#a7f3d0',
        },
        {
          to: '/savings-discovery',
          label: 'Vendor Comparison',
          icon: Sparkles,
        },
        { to: '/reports', label: 'Financial Reports', icon: FileBarChart },
      ],
    });
  }

  // 5. ASSISTANCE
  sections.push({
    title: 'Assistance',
    items: [
      {
        to: '/assistant',
        label: accountType === 'household' ? 'Family AI Assistant' : 'AI Assistant',
        icon: MessageSquare,
        badge: 'Copilot',
        badgeColor: '#7c3aed',
        badgeBg: '#f5f3ff',
        badgeBorder: '#ddd6fe',
      },
    ],
  });

  // 6. ADMINISTRATION (if user has is_admin flag)
  if (user?.is_admin) {
    sections.push({
      title: 'Administration',
      items: [
        {
          to: '/admin',
          label: 'Admin Portal',
          icon: ShieldCheck,
          badge: 'Admin',
          badgeColor: '#dc2626',
          badgeBg: '#fef2f2',
          badgeBorder: '#fecaca',
        },
      ],
    });
  }

  return (
    <aside className={`app-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {accountType === 'individual' ? 'Personal Finance' : accountType === 'household' ? 'Household Finance' : 'Commercial Fintech'}
        </div>
        {mobileOpen && (
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '0.2rem',
              display: 'flex',
              alignItems: 'center',
            }}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="sidebar-menu-list">
        {sections.map((section, sIdx) => (
          <div key={sIdx} className="sidebar-section-group">
            <div className="sidebar-section-title">{section.title}</div>
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} style={{ flexShrink: 0 }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.label}</span>
                  {item.badge && (
                    <span
                      className="sidebar-item-badge"
                      style={
                        item.badgeColor
                          ? {
                              color: item.badgeColor,
                              background: item.badgeBg,
                              border: `1px solid ${item.badgeBorder}`,
                            }
                          : undefined
                      }
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 'var(--radius-md)',
            padding: '0.85rem',
            fontSize: '0.8rem',
            color: '#94a3b8',
            lineHeight: 1.45,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: '#38bdf8',
              fontWeight: 600,
              marginBottom: '0.3rem',
              fontSize: '0.82rem',
            }}
          >
            <ShieldCheck size={15} /> Verified Liquidity
          </div>
          Continuous subscription commitment tracking protects net operating reserves.
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
