import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { path: '/upload', label: 'Upload Scan', icon: '⬆' },
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <span className="logo-icon">🩻</span>
          <h1>RadAssist</h1>
        </div>
        <p className="sidebar-tagline">AI Second Opinion</p>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'sidebar-link--active' : ''}`
            }
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="user-avatar">👤</div>
          <span className="user-name">{user?.name || 'User'}</span>
        </div>
        <button className="btn btn--ghost sidebar-logout" onClick={handleLogout}>
          Sign Out
        </button>
      </div>
    </aside>
  );
}
