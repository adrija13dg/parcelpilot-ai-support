import { useEffect, useState } from 'react';
import { CheckCircle, Clock, Lock, Unlock } from 'lucide-react';
import { api } from '../api/client';
import { useSession } from '../context/SessionContext';

export default function SourcesPage() {
  const { session } = useSession();
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.sources(session).then(setDocs).catch((e) => setError(e.message));
  }, [session]);

  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="sources-page">
      <header className="page-header">
        <div>
          <div className="header-badge">Knowledge base</div>
          <h2>Source Catalog</h2>
          <p>Documents ranked by reliability — lower rank = higher authority</p>
        </div>
      </header>

      <div className="sources-list">
        {docs.map((doc) => (
          <div key={doc.filename} className="source-card glass">
            <div className="source-header">
              {doc.available ? <CheckCircle size={18} className="ok" /> : <Clock size={18} className="pending" />}
              {doc.accessible ? <Unlock size={16} /> : <Lock size={16} />}
              <h3>{doc.title}</h3>
              <span className="rank-badge">Rank {doc.reliability_rank}</span>
            </div>
            <p className="source-meta">
              {doc.doc_type} · {doc.status} · Scope: {doc.customer_scope}
            </p>
            <code>{doc.filename}</code>
          </div>
        ))}
      </div>
    </div>
  );
}
