import { useEffect, useState } from 'react';
import { api } from '../api';

interface LogEntry {
  id: number;
  action: string;
  resource_type: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    api.logs().then(setLogs);
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Audit Logs</h1>
      <p className="text-slate-400 text-sm">
        All user actions, configuration changes, and system events are recorded here.
      </p>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-800">
              <th className="text-left py-3 px-2">Time</th>
              <th className="text-left py-3 px-2">Action</th>
              <th className="text-left py-3 px-2">Resource</th>
              <th className="text-left py-3 px-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-b border-slate-800/50">
                <td className="py-2 px-2 text-slate-400 text-xs whitespace-nowrap">
                  {new Date(l.created_at).toLocaleString()}
                </td>
                <td className="py-2 px-2 font-mono text-xs">{l.action}</td>
                <td className="py-2 px-2 text-slate-400">{l.resource_type || '—'}</td>
                <td className="py-2 px-2 text-xs text-slate-500 max-w-md truncate">
                  {JSON.stringify(l.details)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
