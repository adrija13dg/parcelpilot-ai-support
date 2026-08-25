import { useState } from 'react';
import { Package, Moon, Sun } from 'lucide-react';
import { api } from '../api/client';
import { useSession } from '../context/SessionContext';
import { useTheme } from '../context/ThemeContext';

const ACCOUNTS = [
  { id: 'ACCT-001', name: 'Northstar Logistics' },
  { id: 'ACCT-002', name: 'LumenWorks' },
  { id: 'ACCT-003', name: 'Beacon Retail' },
  { id: 'ACCT-004', name: 'Axis Labs' },
];

export default function LoginPage() {
  const { login } = useSession();
  const { theme, toggle } = useTheme();
  const [role, setRole] = useState('customer');
  const [accountId, setAccountId] = useState('ACCT-001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const session = {
        role: role === 'internal' ? 'support_agent' : 'customer',
        account_id: role === 'customer' ? accountId : null,
      };
      const data = await api.validateSession(session);
      login({ ...session, ...data });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <button type="button" className="theme-toggle floating" onClick={toggle} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      <div className="login-card glass">
        <div className="login-brand">
          <div className="brand-icon">
            <Package size={28} />
          </div>
          <div>
            <h1>ParcelPilot</h1>
            <p>AI Support Portal</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label className="field-label">Role</label>
          <div className="role-grid">
            <button
              type="button"
              className={`role-btn ${role === 'customer' ? 'active' : ''}`}
              onClick={() => setRole('customer')}
            >
              Customer
            </button>
            <button
              type="button"
              className={`role-btn ${role === 'internal' ? 'active' : ''}`}
              onClick={() => setRole('internal')}
            >
              Internal Support
            </button>
          </div>

          {role === 'customer' && (
            <>
              <label className="field-label" htmlFor="account">Account</label>
              <select id="account" value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                {ACCOUNTS.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </>
          )}

          {error && <div className="error-banner">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
