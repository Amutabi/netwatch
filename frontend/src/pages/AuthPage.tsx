import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api, setAuth } from '../api';

export default function AuthPage() {
  const [search] = useSearchParams();
  const isSignup = search.get('mode') === 'signup';
  const [mode, setMode] = useState<'login' | 'signup'>(isSignup ? 'signup' : 'login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'signup') {
        await api.signup({ email, username, password });
        const res = await api.login(username, password);
        setAuth(res.access_token, res.user);
      } else {
        const res = await api.login(username, password);
        setAuth(res.access_token, res.user);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="font-bold text-2xl text-brand-500">NetWatch AI</Link>
          <p className="text-slate-400 mt-2">{mode === 'login' ? 'Sign in to your account' : 'Create an account'}</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {mode === 'signup' && (
            <div>
              <label className="block text-sm text-slate-400 mb-1">Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
          )}
          <div>
            <label className="block text-sm text-slate-400 mb-1">Username</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Sign up'}
          </button>
        </form>

        <p className="text-center text-sm text-slate-400 mt-4">
          {mode === 'login' ? (
            <>No account? <button className="text-brand-500" onClick={() => setMode('signup')}>Sign up</button></>
          ) : (
            <>Have an account? <button className="text-brand-500" onClick={() => setMode('login')}>Sign in</button></>
          )}
        </p>
      </div>
    </div>
  );
}
