import { useEffect, useState } from 'react';
import { Plus, RefreshCw, Trash2 } from 'lucide-react';
import { api, getUser } from '../api';

interface Device {
  id: number;
  name: string;
  hostname: string;
  management_ip: string;
  device_type: string;
  status: string;
  last_seen: string | null;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', hostname: '', management_ip: '', device_type: 'cisco_ios' });
  const user = getUser();
  const isAdmin = user?.role === 'admin';

  useEffect(() => { load(); }, []);

  async function load() {
    setDevices(await api.devices());
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    await fetch('/api/devices', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(form),
    });
    setShowAdd(false);
    setForm({ name: '', hostname: '', management_ip: '', device_type: 'cisco_ios' });
    load();
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Devices</h1>
        <div className="flex gap-2">
          {isAdmin && (
            <>
              <button onClick={() => api.syncTopology()} className="btn-secondary text-sm flex items-center gap-1">
                <RefreshCw size={16} /> Sync GNS3
              </button>
              <button onClick={() => setShowAdd(true)} className="btn-primary text-sm flex items-center gap-1">
                <Plus size={16} /> Add device
              </button>
            </>
          )}
        </div>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="card grid md:grid-cols-2 gap-4">
          <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="input" placeholder="Hostname" value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} required />
          <input className="input" placeholder="Management IP" value={form.management_ip} onChange={(e) => setForm({ ...form, management_ip: e.target.value })} required />
          <select className="input" value={form.device_type} onChange={(e) => setForm({ ...form, device_type: e.target.value })}>
            <option value="cisco_ios">Cisco IOS</option>
            <option value="linux">Linux</option>
          </select>
          <div className="md:col-span-2 flex gap-2">
            <button type="submit" className="btn-primary">Save</button>
            <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-800">
              <th className="text-left py-3 px-2">Name</th>
              <th className="text-left py-3 px-2">IP</th>
              <th className="text-left py-3 px-2">Type</th>
              <th className="text-left py-3 px-2">Status</th>
              <th className="text-left py-3 px-2">Last seen</th>
              {isAdmin && <th className="text-right py-3 px-2">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                <td className="py-3 px-2 font-medium">{d.name}</td>
                <td className="py-3 px-2 text-slate-400">{d.management_ip}</td>
                <td className="py-3 px-2 text-slate-400">{d.device_type}</td>
                <td className="py-3 px-2">
                  <StatusBadge status={d.status} />
                </td>
                <td className="py-3 px-2 text-slate-400 text-xs">
                  {d.last_seen ? new Date(d.last_seen).toLocaleString() : '—'}
                </td>
                {isAdmin && (
                  <td className="py-3 px-2 text-right">
                    <button
                      onClick={() => api.devices().then(() => fetch(`/api/devices/${d.id}`, {
                        method: 'DELETE',
                        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
                      }).then(load))}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    up: 'bg-green-900/50 text-green-400',
    down: 'bg-red-900/50 text-red-400',
    unknown: 'bg-slate-800 text-slate-400',
    removed: 'bg-slate-800 text-slate-500 line-through',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${colors[status] || colors.unknown}`}>
      {status}
    </span>
  );
}
