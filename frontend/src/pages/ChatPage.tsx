import { useEffect, useRef, useState } from 'react';
import { Send, Check, X } from 'lucide-react';
import { api, getUser } from '../api';

interface Message {
  id?: number;
  role: string;
  content: string;
}

interface Conversation {
  id: number;
  title: string;
}

interface ConfigRequest {
  id: number;
  natural_language_request: string;
  proposed_commands: string[];
  status: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [pendingConfigs, setPendingConfigs] = useState<ConfigRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const user = getUser();
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    api.conversations().then(setConversations);
    if (isAdmin) api.configRequests('pending').then(setPendingConfigs);
  }, [isAdmin]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const res = await api.chat(userMsg, conversationId);
      setConversationId(res.conversation_id);
      setMessages((m) => [...m, { role: 'assistant', content: res.response }]);
      if (isAdmin) setPendingConfigs(await api.configRequests('pending'));
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, something went wrong.' }]);
    } finally {
      setLoading(false);
    }
  }

  async function loadConversation(id: number) {
    setConversationId(id);
    const msgs = await api.messages(id);
    setMessages(msgs);
  }

  const suggestions = [
    "What's the network status?",
    'Any alerts right now?',
    'Enable port 1 on router1',
    'Generate network report',
  ];

  return (
    <div className="flex h-[calc(100vh-0px)]">
      <aside className="w-64 border-r border-slate-800 p-3 overflow-y-auto hidden md:block">
        <h2 className="text-sm font-semibold text-slate-400 mb-3">History</h2>
        <button
          onClick={() => { setConversationId(undefined); setMessages([]); }}
          className="w-full text-left text-sm px-2 py-1.5 rounded hover:bg-slate-800 text-brand-500 mb-2"
        >
          + New chat
        </button>
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => loadConversation(c.id)}
            className={`w-full text-left text-sm px-2 py-1.5 rounded truncate ${
              conversationId === c.id ? 'bg-slate-800' : 'hover:bg-slate-800/50'
            }`}
          >
            {c.title}
          </button>
        ))}
      </aside>

      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h1 className="text-xl font-bold">NetWatch AI Assistant</h1>
          <p className="text-sm text-slate-400">Ask about network status, faults, or request configuration changes</p>
        </div>

        {isAdmin && pendingConfigs.length > 0 && (
          <div className="p-4 bg-yellow-950/30 border-b border-yellow-900/50">
            <p className="text-sm font-medium text-yellow-400 mb-2">Pending config approvals</p>
            {pendingConfigs.map((req) => (
              <div key={req.id} className="card mb-2 !p-3">
                <p className="text-sm mb-1">{req.natural_language_request}</p>
                <pre className="text-xs text-slate-400 bg-slate-950 p-2 rounded mb-2 overflow-x-auto">
                  {req.proposed_commands.join('\n')}
                </pre>
                <div className="flex gap-2">
                  <button
                    onClick={async () => {
                      await api.approveConfig(req.id);
                      setPendingConfigs(await api.configRequests('pending'));
                    }}
                    className="btn-primary text-xs flex items-center gap-1"
                  >
                    <Check size={14} /> Approve & execute
                  </button>
                  <button
                    onClick={async () => {
                      await api.rejectConfig(req.id);
                      setPendingConfigs(await api.configRequests('pending'));
                    }}
                    className="btn-secondary text-xs flex items-center gap-1"
                  >
                    <X size={14} /> Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <p className="text-slate-400 mb-4">Try asking:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => setInput(s)}
                    className="text-sm px-3 py-1.5 rounded-full border border-slate-700 hover:border-brand-500 text-slate-300"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-2 text-sm ${
                m.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-800 text-slate-200'
              }`}>
                <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
              </div>
            </div>
          ))}
          {loading && <p className="text-slate-500 text-sm">Thinking...</p>}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={sendMessage} className="p-4 border-t border-slate-800 flex gap-2">
          <input
            className="input flex-1"
            placeholder="Ask in plain English..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
