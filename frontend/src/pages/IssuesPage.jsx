import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp, Users, Copy, Bug } from 'lucide-react';
import { api } from '../api/client';
import { useSession } from '../context/SessionContext';

export default function IssuesPage() {
  const { session } = useSession();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.issues(session).then(setData).catch((e) => setError(e.message));
  }, [session]);

  const investigate = (question) => {
    navigate('/chat', { state: { prefill: question } });
  };

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <div className="loading-state">Loading Ops Radar…</div>;

  const metrics = [
    { label: 'SLA risk', value: data.sla_risk_count, icon: AlertTriangle, color: 'red' },
    { label: 'Volume spikes', value: data.volume_spike_count ?? 0, icon: TrendingUp, color: 'amber' },
    { label: 'Duplicate clusters', value: data.duplicate_cluster_count ?? 0, icon: Copy, color: 'blue' },
    { label: 'Known issue hits', value: data.known_issue_count ?? 0, icon: Bug, color: 'green' },
    { label: 'Customers affected', value: data.customers_affected, icon: Users, color: 'green' },
  ];

  return (
    <div className="issues-page">
      <header className="page-header">
        <div>
          <div className="header-badge">Operations</div>
          <h2>Ops Radar</h2>
          <p>Proactive issue detection · Snapshot {data.snapshot_time}</p>
        </div>
      </header>

      {!session.is_internal && (
        <div className="info-banner">Full Ops Radar is available to Internal Support users.</div>
      )}

      <div className="metrics-grid">
        {metrics.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className={`metric-card glass ${color}`}>
            <Icon size={20} />
            <div>
              <span className="metric-value">{value}</span>
              <span className="metric-label">{label}</span>
            </div>
          </div>
        ))}
      </div>

      {data.known_issue_matches?.length > 0 && (
        <section className="section glass">
          <h3>Known product issue matches</h3>
          {data.known_issue_matches.map((ki) => (
            <div key={ki.known_issue_id} className="issue-row">
              <div>
                <strong>{ki.known_issue_id}</strong> — {ki.title}
                <span className="badge info">{ki.status}</span>
                <p>
                  Tickets: {ki.ticket_ids.join(', ')} · {ki.customers_affected} customer(s)
                </p>
                <p className="muted">Workaround: {ki.workaround}</p>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() =>
                  investigate(
                    `Investigate ${ki.known_issue_id} (${ki.title}) for tickets ${ki.ticket_ids.join(', ')}.`
                  )
                }
              >
                Investigate with AI
              </button>
            </div>
          ))}
        </section>
      )}

      {data.volume_spikes?.length > 0 && (
        <section className="section glass">
          <h3>Category volume spikes</h3>
          {data.volume_spikes.map((spike) => (
            <div key={spike.theme} className="issue-row">
              <div>
                <strong>{spike.theme}</strong>
                <span className={`badge ${spike.severity === 'high' ? 'danger' : 'warn'}`}>
                  +{spike.spike_pct}% vs closed baseline
                </span>
                <p>
                  {spike.open_count} open vs {spike.closed_baseline} recent closed in category
                </p>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => investigate(`Analyze the volume spike in '${spike.theme}' — why are open tickets elevated?`)}
              >
                Investigate with AI
              </button>
            </div>
          ))}
        </section>
      )}

      {data.duplicate_clusters?.length > 0 && (
        <section className="section glass">
          <h3>Duplicate / similar ticket clusters</h3>
          {data.duplicate_clusters.map((c) => (
            <div key={c.cluster_key} className="issue-row">
              <div>
                <strong>{c.sample_subject}</strong>
                <p>
                  {c.ticket_ids.join(', ')} · {c.open_count} open · Accounts: {c.accounts.join(', ')}
                </p>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() =>
                  investigate(`Are tickets ${c.ticket_ids.join(', ')} duplicates of the same underlying issue?`)
                }
              >
                Investigate with AI
              </button>
            </div>
          ))}
        </section>
      )}

      {data.sla_risk_tickets?.length > 0 && (
        <section className="section glass">
          <h3>SLA risk tickets</h3>
          {data.sla_risk_tickets.map((t) => (
            <div key={t.ticket_id} className="issue-row">
              <div>
                <strong>{t.ticket_id}</strong> — {t.subject}
                <p>
                  Severity {t.sla_status?.severity} · {t.sla_status?.elapsed_minutes} min elapsed
                  {t.sla_status?.breached && <span className="badge danger">BREACHED</span>}
                </p>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() =>
                  investigate(`Analyze ticket ${t.ticket_id}: severity, SLA status, and whether we should escalate.`)
                }
              >
                Investigate with AI
              </button>
            </div>
          ))}
        </section>
      )}

      <section className="section glass">
        <h3>Recurring themes</h3>
        {data.recurring_issues?.map((issue) => (
          <div key={issue.theme} className="issue-row">
            <div>
              <strong>{issue.theme}</strong>
              <p>
                {issue.open_count} open · {issue.customers_affected} customer(s) · {issue.ticket_ids?.join(', ')}
              </p>
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() =>
                investigate(`Investigate the '${issue.theme}' issue across tickets ${issue.ticket_ids?.join(', ')}.`)
              }
            >
              Investigate with AI
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}
