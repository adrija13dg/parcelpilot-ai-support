export default function EscalationModal({ pending, onConfirm, onCancel, loading }) {
  if (!pending) return null;

  return (
    <div className="modal-overlay">
      <div className="modal glass">
        <h3>Confirm escalation</h3>
        <p className="modal-sub">Review before creating the escalation record.</p>
        <dl className="escalation-details">
          <div><dt>Ticket</dt><dd>{pending.ticket_id}</dd></div>
          <div><dt>Account</dt><dd>{pending.account_name}</dd></div>
          <div><dt>Severity</dt><dd>{pending.severity}</dd></div>
          <div><dt>Reason</dt><dd>{pending.reason}</dd></div>
        </dl>
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button type="button" className="btn-primary" onClick={onConfirm} disabled={loading}>
            {loading ? 'Creating…' : 'Confirm escalation'}
          </button>
        </div>
      </div>
    </div>
  );
}
