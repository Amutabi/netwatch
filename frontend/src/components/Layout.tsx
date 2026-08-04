import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Server, MessageSquare, FileText, ScrollText, Settings, LogOut, Bell,
} from 'lucide-react';
import { clearAuth, getUser } from '../api';

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/devices', label: 'Devices', icon: Server },
  { to: '/chat', label: 'AI Chat', icon: MessageSquare },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/logs', label: 'Logs', icon: ScrollText },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const user = getUser();

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <Link to="/dashboard" className="font-bold text-lg text-brand-500">NetWatch AI</Link>
          <p className="text-xs text-slate-500 mt-1">GNS3 Network Monitor</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                location.pathname === to
                  ? 'bg-brand-600/20 text-brand-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-800">
          <div className="text-xs text-slate-500 mb-2 truncate">{user?.username} ({user?.role})</div>
          <button
            onClick={() => { clearAuth(); navigate('/'); }}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-red-400 w-full px-2 py-1"
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

export function AlertBanner({ alerts }: { alerts: { severity: string; title: string; message: string }[] }) {
  if (!alerts.length) return null;
  return (
    <div className="bg-red-950/50 border-b border-red-900 px-6 py-2 flex items-center gap-2 text-sm">
      <Bell size={16} className="text-red-400 shrink-0" />
      <span className="text-red-200">{alerts[0].title}: {alerts[0].message}</span>
      {alerts.length > 1 && <span className="text-red-400">+{alerts.length - 1} more</span>}
    </div>
  );
}
