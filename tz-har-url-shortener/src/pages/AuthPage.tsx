import { Link2, Loader2, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { useUser } from "../context/AuthContext";
import { useUrlTags } from "../context/TagContext";
import { api } from "../services/TzHarApi";
import { useView } from "../context/ViewContext";
import { asyncWrapper } from "../util/asyncWrapper";
import type { User } from "../types/user";
import type { Pagination } from "../types/pagination";
import type { UrlTag } from "../types/URL";
import { useDialog } from "../hooks/useDialog";

const AuthPage = () => {
  const { showAlert, AlertRenderer, ConfirmRenderer } = useDialog();
  const { setUser } = useUser();
  const { tags, setTags } = useUrlTags();
  const { view, setView } = useView();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchingUser, setFetchingUser] = useState(false);
  const [showPassword, setShowPassword] = useState(false); // Novo state

  const loadTags = async () => {
    if (tags.length > 0) return;
    const { data, error } = await asyncWrapper<Pagination<UrlTag>>(
      async () => await api.tag.getUserTags()
    );
    if (data) setTags(data.results);
    if (error) console.log(error);
  };

  const init = async () => {
    setFetchingUser(true);
    const { data, error } = await asyncWrapper<User>(async () => await api.auth.getMe());
    if (data) {
      setUser(data);
      await loadTags();
      setView("urls");
    } else {
      console.log(error);
    }
    setFetchingUser(false);
  };

  useEffect(() => {
    init();
  }, []);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const userData = await api.auth.login(email, password);
      setUser(userData);
      await loadTags();
      setView("urls");
    } catch (error: any) {
      showAlert("Login failed, invalid email or password");
    }
    setLoading(false);
  };

  const handleSignup = async () => {
    setLoading(true);
    try {
      await api.auth.signup(email, password);
      const userData = await api.auth.login(email, password);
      setUser(userData);
      setView("urls");
    } catch (error: any) {
      if (error.message.includes("Email")) {
        showAlert("Signup failed: " + error.message);
      } else {
        showAlert("Signup failed");
      }
    }
    setLoading(false);
  };

  if (fetchingUser) {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center bg-slate-50 text-slate-700">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
        <p className="text-lg font-medium">Fetching session information...</p>
        <p className="text-sm text-slate-500 mt-1">Please wait while we check your account.</p>
      </div>
    );
  }

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

        {/* Toggle View Buttons */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setView("login")}
            className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
              view === "login"
                ? "bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setView("signup")}
            className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
              view === "signup"
                ? "bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98"
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && (view === "login" ? handleLogin() : handleSignup())
              }
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              placeholder="you@example.com"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && (view === "login" ? handleLogin() : handleSignup())
                }
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none pr-12"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={view === "login" ? handleLogin : handleSignup}
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md active:scale-98"
          >
            {loading ? "Loading..." : view === "login" ? "Login" : "Create Account"}
          </button>
        </div>
      </div>
      {AlertRenderer}
      {ConfirmRenderer}
    </div>
  );
};

export default AuthPage;
