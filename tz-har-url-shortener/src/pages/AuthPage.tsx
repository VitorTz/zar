import { Link2 } from "lucide-react";
import { useState } from "react";
import { useUser } from "../context/AuthContext";
import { useUrlTags } from "../context/TagContext";
import { api } from "../services/TzHarApi";
import { useView } from "../context/ViewContext";



const AuthPage = () => {

  const {setUser} = useUser()
  const { setTags } = useUrlTags()
  const { view, setView } = useView()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true);
    try {
      const userData = await api.auth.login(email, password);
      const tags = await api.tag.getUserTags()
      setTags(tags.results)
      setUser(userData);
      setView('urls');
    } catch (error: any) {
      alert('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSignup = async () => {
    setLoading(true);
    try {
      await api.auth.signup(email, password);
      const userData = await api.auth.login(email, password);
      setUser(userData);
      setView('urls');
    } catch (error: any) {
      alert('Signup failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4">
              <Link2 className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900">TzHar URL</h1>
            <p className="text-slate-600 mt-2">Shorten and manage your links</p>
          </div>

          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setView('login')}
              className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                view === 'login'
                  ? 'bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setView('signup')}
              className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                view === 'signup'
                  ? 'bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98'
              }`}
            >
              Sign Up
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (view === 'login' ? handleLogin() : handleSignup())}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (view === 'login' ? handleLogin() : handleSignup())}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                placeholder="••••••••"
              />
            </div>
            <button
              onClick={view === 'login' ? handleLogin : handleSignup}
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md active:scale-98"
            >
              {loading ? 'Loading...' : view === 'login' ? 'Login' : 'Create Account'}
            </button>
          </div>
        </div>
      </div>
    );
};


export default AuthPage