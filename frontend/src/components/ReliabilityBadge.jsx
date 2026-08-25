export default function ReliabilityBadge({ reliability }) {
  if (!reliability) return null;

  const level = reliability.level || 'medium';
  const cls = `reliability-badge ${level}`;

  return (
    <div className={cls} title={reliability.reasons?.join('\n')}>
      <span className="reliability-dot" />
      {reliability.label || `${level} reliability`}
      {reliability.reasons?.length > 0 && (
        <details className="reliability-details">
          <summary>Why?</summary>
          <ul>
            {reliability.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
