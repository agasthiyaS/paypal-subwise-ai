import React from 'react';
import { NavLink } from 'react-router-dom';
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
} from 'lucide-react';

const Sidebar = () => {
  const menuItems = [
    { to: '/dashboard', label: 'Main Dashboard', icon: LayoutDashboard },
    { to: '/subscriptions', label: 'Subscription Manager', icon: Layers },
    { to: '/forecast', label: 'Cash Flow Forecast', icon: LineChart },
    { to: '/simulator', label: 'Scenario Simulator', icon: Sliders },
    { to: '/recommendations', label: 'AI Recommendations', icon: Sparkles, badge: '4 New' },
    { to: '/reports', label: 'Financial Reports', icon: FileBarChart },
    { to: '/assistant', label: 'AI Assistant', icon: MessageSquare, badge: 'New', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
  ];

  return (
    <aside className="app-sidebar">
      <div className="sidebar-header">
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Fintech Navigation
        </div>
      </div>

      <nav className="sidebar-menu-list">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={22} />
              <span>{item.label}</span>
              {item.badge && (
                <span
                  className="sidebar-item-badge"
                  style={item.badgeColor ? {
                    color: item.badgeColor,
                    background: item.badgeBg,
                    border: `1px solid ${item.badgeBorder}`,
                  } : undefined}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 'var(--radius-md)',
          padding: '1.15rem',
          fontSize: '0.92rem',
          color: '#cbd5e1',
          lineHeight: 1.55
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8', fontWeight: 700, marginBottom: '0.45rem', fontSize: '0.95rem' }}>
            <ShieldCheck size={18} /> Solvency Assurance
          </div>
          Continuous subscription commitment tracking protects SMB operating liquidity.
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
