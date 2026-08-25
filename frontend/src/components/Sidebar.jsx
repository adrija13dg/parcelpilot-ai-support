import { NavLink } from 'react-router-dom';
import { MessageSquare, BarChart3, BookOpen, LogOut, Moon, Sun, Package } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useTheme } from '../context/ThemeContext';

export default function Sidebar() {
  const { session, logout } = useSession();
  const { theme, toggle } = useTheme();

  const nav = [
    { to: '/chat', icon: MessageSquare, label: 'Chat' },
    { to: '/issues', icon: BarChart3, label: 'Ops Radar' },
    { to: '/sources', icon: BookOpen, label: 'Sources' },
  ];

  return (
    <aside className="sidebar glass">
      <div className="sidebar-brand">
        <Package size={22} />
        <div>
          <strong>ParcelPilot</strong>
          <span>Support AI</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="session-chip">
          <span className="chip-label">{session.is_internal ? 'Internal' : 'Customer'}</span>
          <span className="chip-value">{session.account_name || 'All accounts'}</span>
        </div>
        <button type="button" className="icon-btn" onClick={toggle} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <button type="button" className="icon-btn danger" onClick={logout} aria-label="Sign out">
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
}
