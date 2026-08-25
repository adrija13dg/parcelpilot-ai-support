import { Wrench } from 'lucide-react';

export default function ToolTrace({ trace }) {
  if (!trace?.length) return null;

  return (
    <details className="tool-trace glass">
      <summary>
        <Wrench size={14} />
        Tool activity ({trace.length})
      </summary>
      <div className="tool-list">
        {trace.map((item, i) => (
          <div key={i} className="tool-item">
            <strong>{item.tool}</strong>
            <pre>{JSON.stringify(item.arguments, null, 2)}</pre>
          </div>
        ))}
      </div>
    </details>
  );
}
