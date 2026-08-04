import { Link } from 'react-router-dom';
import { Activity, Shield, Bot, Network, ArrowRight } from 'lucide-react';

const features = [
  {
    icon: Activity,
    title: 'Live Monitoring',
    desc: 'ICMP/SNMP polling every 30s with latency, reachability, and interface metrics.',
  },
  {
    icon: Bot,
    title: 'AI Chatbot',
    desc: 'Ask in plain English: "What\'s the network status?" or "Enable port 3 on switch1".',
  },
  {
    icon: Shield,
    title: 'Admin-Gated SSH',
    desc: 'Configuration changes require admin approval before execution via Netmiko.',
  },
  {
    icon: Network,
    title: 'Topology Sync',
    desc: 'Auto-discover devices from GNS3 API. Removed nodes are cleaned from inventory.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="font-bold text-xl text-brand-500">NetOps Assistant</span>
          <div className="flex gap-3">
            <Link to="/auth" className="btn-secondary text-sm">Sign in</Link>
            <Link to="/auth?mode=signup" className="btn-primary text-sm">Get started</Link>
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-6">
          Network monitoring with an{' '}
          <span className="text-brand-500">AI assistant</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
          Monitor your Enterprise network, detect faults, get recommendations, and configure
          devices over SSH — all through a simple conversational interface.
        </p>
        <Link to="/auth?mode=signup" className="btn-primary inline-flex items-center gap-2 text-lg px-6 py-3">
          Start monitoring <ArrowRight size={20} />
        </Link>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="card">
            <Icon className="text-brand-500 mb-3" size={28} />
            <h3 className="font-semibold mb-2">{title}</h3>
            <p className="text-sm text-slate-400">{desc}</p>
          </div>
        ))}
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="card bg-slate-900/50">
          <h2 className="text-2xl font-bold mb-4">Built for Enterprise Network</h2>
          <p className="text-slate-400 mb-4">
          </p>
          <ul className="text-sm text-slate-400 space-y-2 list-disc list-inside">
            <li>Dashboard with charts, device list, and alert feed</li>
            <li>Downloadable PDF/CSV network reports</li>
            <li>Conversation history and full audit logs</li>
            <li>Fault detection with actionable recommendations</li>
          </ul>
        </div>
      </section>

      <footer className="border-t border-slate-800 py-8 text-center text-sm text-slate-500">
        NetOps Assistant — Network Monitoring & Configuration Chatbot
      </footer>
    </div>
  );
}
