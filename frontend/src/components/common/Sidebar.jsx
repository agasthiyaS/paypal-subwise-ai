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
  User,
  Building2,
  ShoppingCart,
  Zap,
  Activity,
  Search,
} from 'lucide-react';

const Sidebar = () => {
  const { user, business } = useAuth();
  const accountType = business?.account_type || 'business';

  let menuItems = [];
  let headerLabel = 'Fintech Navigation';
  let footerTitle = 'Solvency Assurance';
  let footerDesc = 'Continuous subscription commitment tracking protects SMB operating liquidity.';

  if (accountType === 'individual') {
    headerLabel = 'Personal Intelligence';
    footerTitle = 'Savings Assurance';
    footerDesc = 'Automated recurring expense monitoring keeps you ahead of silent subscription leaks.';
    menuItems = [
      { to: '/dashboard', label: 'Personal Dashboard', icon: LayoutDashboard },
      { to: '/expenses', label: 'Income & Expenses', icon: TrendingDown },
      { to: '/insights', label: 'AI Insights', icon: Activity, badge: 'New', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
      { to: '/savings-discovery', label: 'Savings Discovery', icon: Sparkles, badge: 'AI', badgeColor: '#059669', badgeBg: '#ecfdf5', badgeBorder: '#a7f3d0' },
      { to: '/subscriptions', label: 'Subscriptions & Apps', icon: Layers },
      { to: '/forecast', label: 'Cash Flow & Income', icon: LineChart },
      { to: '/recommendations', label: 'AI Savings Advice', icon: Sparkles, badge: 'Tailored', badgeColor: '#059669', badgeBg: '#ecfdf5', badgeBorder: '#a7f3d0' },
      { to: '/assistant', label: 'Savings Assistant', icon: MessageSquare, badge: 'AI', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
      { to: '/reports', label: 'Spending Reports', icon: FileBarChart },
    ];
  } else if (accountType === 'household') {
    headerLabel = 'Household Intelligence';
    footerTitle = 'Household Budgeting';
    footerDesc = 'Compare grocery prices, detect utility spikes, and streamline shared living costs.';
    menuItems = [
      { to: '/dashboard', label: 'Household Overview', icon: LayoutDashboard },
      { to: '/household', label: 'Household Workspace', icon: Home },
      { to: '/expenses', label: 'Shared Expenses', icon: TrendingDown },
      { to: '/insights', label: 'AI Insights', icon: Activity, badge: 'New', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
      { to: '/savings-discovery', label: 'Savings Discovery', icon: Sparkles, badge: 'AI', badgeColor: '#059669', badgeBg: '#ecfdf5', badgeBorder: '#a7f3d0' },
      { to: '/subscriptions', label: 'Shared Subscriptions', icon: Layers },
      { to: '/forecast', label: 'Household Cash Flow', icon: LineChart },
      { to: '/recommendations', label: 'Grocery & Utility AI', icon: Sparkles, badge: 'Deals', badgeColor: '#d97706', badgeBg: '#fef3c7', badgeBorder: '#fde68a' },
      { to: '/assistant', label: 'Family AI Assistant', icon: MessageSquare, badge: 'AI', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
      { to: '/reports', label: 'Shared Bill Reports', icon: FileBarChart },
    ];
  } else {
    // Small Business
    headerLabel = 'Fintech Navigation';
    footerTitle = 'Solvency Assurance';
    footerDesc = 'Continuous subscription commitment tracking protects SMB operating liquidity.';
    menuItems = [
      { to: '/dashboard', label: 'Main Dashboard', icon: LayoutDashboard },
      { to: '/subscriptions', label: 'Subscription Manager', icon: Layers },
      { to: '/forecast', label: 'Cash Flow Forecast', icon: LineChart },
      { to: '/simulator', label: 'Scenario Simulator', icon: Sliders },
      { to: '/recommendations', label: 'AI Recommendations', icon: Sparkles, badge: '4 New' },
      { to: '/savings-discovery', label: 'Vendor Comparison', icon: Sparkles, badge: 'AI', badgeColor: '#059669', badgeBg: '#ecfdf5', badgeBorder: '#a7f3d0' },
      { to: '/reports', label: 'Financial Reports', icon: FileBarChart },
      { to: '/assistant', label: 'AI Assistant', icon: MessageSquare, badge: 'New', badgeColor: '#7c3aed', badgeBg: '#f5f3ff', badgeBorder: '#e9d5ff' },
    ];
  }

  if (user?.is_admin) {
    menuItems.push({
      to: '/admin',
      label: 'Admin Portal',
      icon: ShieldCheck,
      badge: 'Admin',
      badgeColor: '#ef4444',
      badgeBg: '#fef2f2',
      badgeBorder: '#fecaca',
    });
  }

  return (
    <aside className="app-sidebar">
      <div className="sidebar-header">
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {headerLabel}
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
            <ShieldCheck size={18} /> {footerTitle}
          </div>
          {footerDesc}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
