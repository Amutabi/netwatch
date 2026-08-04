import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { api, getToken } from '../api';

export default function ReportsPage() {
  const [data, setData] = useState<{
    generated_at: string;
    device_count: number;
    devices_up: number;
    alert_count: number;
    devices: { name: string; ip: string; status: string; avg_latency_ms: number | null }[];
    alerts: { severity: string; title: string; message: string }[];
  } | null>(null);
  const [hours, setHours] = useState(24);

  useEffect(() => {
    api.reportData(hours).then(setData);
  }, [hours]);

  function download(format: 'csv' | 'pdf') {
    const token = getToken();
    const url = `${api.downloadReport(format, hours)}&token=${token}`;
    window.open(url.replace('&token=', ''), '_blank');
    fetch(api.downloadReport(format, hours), {
      headers: { Authorization: `Bearer ${token}` },
    }).then((r) => r.blob()).then((blob) => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `netwatch-report.${format}`;
      a.click();
    });
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Network Reports</h1>
        <div className="flex items-center gap-3">
          <select className="input w-auto" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
          </select>
          <button onClick={() => download('csv')} className="btn-secondary text-sm flex items-center gap-1">
            <Download size={16} /> CSV
          </button>
          <button onClick={() => download('pdf')} className="btn-primary text-sm flex items-center gap-1">
            <Download size={16} /> PDF
          </button>
        </div>
      </div>

      {data && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold">{data.devices_up}/{data.device_count}</p>
              <p className="text-sm text-slate-400">Devices online</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold">{data.alert_count}</p>
              <p className="text-sm text-slate-400">Alerts in period</p>
            </div>
            <div className="card text-center">
              <p className="text-sm text-slate-400">Generated</p>
              <p className="text-sm">{new Date(data.generated_at).toLocaleString()}</p>
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-4">Device Summary</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-800">
                  <th className="text-left py-2">Device</th>
                  <th className="text-left py-2">IP</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {data.devices.map((d) => (
                  <tr key={d.name} className="border-b border-slate-800/50">
                    <td className="py-2">{d.name}</td>
                    <td className="py-2 text-slate-400">{d.ip}</td>
                    <td className="py-2">{d.status}</td>
                    <td className="py-2">{d.avg_latency_ms != null ? `${d.avg_latency_ms} ms` : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.alerts.length > 0 && (
            <div className="card">
              <h2 className="font-semibold mb-4">Alerts</h2>
              <div className="space-y-2">
                {data.alerts.map((a, i) => (
                  <div key={i} className="text-sm border-l-2 border-yellow-500 pl-3">
                    <span className="text-yellow-400 uppercase text-xs">{a.severity}</span>
                    <p className="font-medium">{a.title}</p>
                    <p className="text-slate-400">{a.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
