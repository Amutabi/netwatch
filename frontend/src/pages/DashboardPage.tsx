import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity, Server, AlertTriangle, CheckCircle } from 'lucide-react';
import { api, connectAlerts, getToken } from '../api';
import { AlertBanner } from '../components/Layout';

interface Stats {
  total_devices: number;
  devices_up: number;
  devices_down: number;
  active_alerts: number;
  critical_alerts: number;
}

interface Device {
  id: number;
  name: string;
  management_ip: string;
  status: string;
}

interface Alert {
  id: number;
  severity: string;
  title: string;
  message: string;
  recommendation?: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [chartData, setChartData] = useState<{ time: string; latency: number }[]>([]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    let ws: WebSocket | null = null;
    if (getToken()) {
      ws = connectAlerts((data: { type?: string; alerts?: Alert[] }) => {
        if (data.type === 'alerts' && data.alerts) setAlerts(data.alerts);
      });
    }
    return () => { clearInterval(interval); ws?.close(); };
  }, []);

  async function loadData() {
    try {
      const [s, d, a] = await Promise.all([
        api.dashboardStats(),
        api.devices(),
        api.alerts(),
      ]);
      setStats(s);
      setDevices(d);
      setAlerts(a.slice(0, 5));

      if (d.length > 0) {
        const metrics = await api.deviceMetrics(d[0].id);
        setChartData(
          metrics.map((m: { recorded_at: string; value: number }) => ({
            time: new Date(m.recorded_at).toLocaleTimeString(),
            latency: m.value,
          }))
        );
      }
    } catch {}
  }

  const statCards = stats ? [
    { label: 'Total Devices', value: stats.total_devices, icon: Server, color: 'text-brand-500' },
    { label: 'Online', value: stats.devices_up, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Offline', value: stats.devices_down, icon: Activity, color: 'text-red-400' },
    { label: 'Active Alerts', value: stats.active_alerts, icon: AlertTriangle, color: 'text-yellow-400' },
  ] : [];

  return (
    <div>
      <AlertBanner alerts={alerts} />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <button onClick={() => api.poll()} className="btn-secondary text-sm">Poll now</button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card flex items-center gap-4">
              <Icon className={color} size={32} />
              <div>
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-sm text-slate-400">{label}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold mb-4">
              Latency — {devices[0]?.name || 'No devices'}
            </h2>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} unit=" ms" />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                  <Line type="monotone" dataKey="latency" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-500 text-sm py-8 text-center">Add devices to see metrics</p>
            )}
          </div>

          <div className="card">
            <h2 className="font-semibold mb-4">Recent Alerts</h2>
            <div className="space-y-3 max-h-56 overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="text-slate-500 text-sm">No active alerts</p>
              ) : alerts.map((a) => (
                <div key={a.id} className="border-l-2 border-yellow-500 pl-3 py-1">
                  <p className="text-sm font-medium">{a.title}</p>
                  <p className="text-xs text-slate-400">{a.message}</p>
                  {a.recommendation && (
                    <p className="text-xs text-brand-500 mt-1">{a.recommendation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-4">Devices</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800">
                <th className="text-left py-2">Name</th>
                <th className="text-left py-2">IP</th>
                <th className="text-left py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id} className="border-b border-slate-800/50">
                  <td className="py-2">{d.name}</td>
                  <td className="py-2 text-slate-400">{d.management_ip}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      d.status === 'up' ? 'bg-green-900/50 text-green-400' :
                      d.status === 'down' ? 'bg-red-900/50 text-red-400' :
                      'bg-slate-800 text-slate-400'
                    }`}>{d.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
