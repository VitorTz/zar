import { useEffect, useState } from "react";
import {
  Link2,
  Users,
  MousePointerClick,
  Activity,
  TrendingUp,
  Globe,
  Monitor,
  Tag,
  Globe2,
  Calendar,
  Shield,
  Target,
  RefreshCw,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Dashboard } from "../types/dashboard";
import { asyncWrapper } from "../util/asyncWrapper";
import { api } from "../services/TzHarApi";
import { useDialog } from "../hooks/useDialog";

const COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
];

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { showAlert, AlertRenderer } = useDialog();

  const init = async () => {
    if (dashboard) { return }
    setIsLoading(true);
    const { data, error } = await asyncWrapper<Dashboard>(
      async () => await api.dashboard.getDashboard()
    );
    if (data) { setDashboard(data); }
    if (error) { showAlert("Erro ao buscar dados"); }
    setIsLoading(false);
  };

  useEffect(() => {
    init();
  }, []);

  if (!dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-500">Carregando...</div>
      </div>
    );
  }

  const deviceData = [
    { name: "Mobile", value: dashboard.client_info.devices.mobile },
    { name: "Desktop", value: dashboard.client_info.devices.desktop },
    { name: "Tablet", value: dashboard.client_info.devices.tablet },
    { name: "Outro", value: dashboard.client_info.devices.other },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-slate-900">Dashboard</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={init}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-400 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
            />
            <span>{isLoading ? "Refreshing..." : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* Cards Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
              <Link2 className="w-6 h-6 text-indigo-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-600">Total URLs</p>
              <p className="text-2xl font-bold text-slate-900">
                {dashboard.total_urls.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                +{dashboard.urls.new_24h} in the Last 24h
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-600">Users</p>
              <p className="text-2xl font-bold text-slate-900">
                {dashboard.users.total.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {dashboard.users.active_24h} active in 24h
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center">
              <MousePointerClick className="w-6 h-6 text-pink-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-600">Total clicks</p>
              <p className="text-2xl font-bold text-slate-900">
                {dashboard.clicks.total.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                +{dashboard.clicks.last_24h} in the Last 24h
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-600">Visitantes Únicos</p>
              <p className="text-2xl font-bold text-slate-900">
                {dashboard.analytics.unique_visitors_all_time.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {dashboard.analytics.unique_visitors_30d.toLocaleString()} in 30 Days
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Estatísticas de Conversão */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Target className="w-5 h-5" />
            <p className="text-sm opacity-90">Conversion Rate</p>
          </div>
          <p className="text-3xl font-bold">
            {dashboard.conversion.conversion_rate.toFixed(1)}%
          </p>
          <p className="text-xs opacity-75 mt-2">
            URLs with Clicks in the Last 30 Days
          </p>
        </div>

        <div className="bg-gradient-to-br from-pink-500 to-rose-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5" />
            <p className="text-sm opacity-90">Popular Urls</p>
          </div>
          <p className="text-3xl font-bold">
            {dashboard.conversion.urls_10plus_rate.toFixed(1)}%
          </p>
          <p className="text-xs opacity-75 mt-2">With 10+ Clicks</p>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Globe className="w-5 h-5" />
            <p className="text-sm opacity-90">Global Reach</p>
          </div>
          <p className="text-3xl font-bold">
            {dashboard.analytics.countries_reached}
          </p>
          <p className="text-xs opacity-75 mt-2">Countries Reached</p>
        </div>
      </div>

      {/* Crescimento Diário */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Calendar className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-slate-900">
            Growth in the Last 7 Days
          </h3>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dashboard.daily_growth}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              tickFormatter={(value) =>
                new Date(value).toLocaleDateString("pt-BR", {
                  day: "2-digit",
                  month: "2-digit",
                })
              }
            />
            <YAxis stroke="#64748b" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
              }}
              labelFormatter={(value) =>
                new Date(value).toLocaleDateString("pt-BR")
              }
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="new_urls"
              stroke="#6366f1"
              name="New URLs"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="new_users"
              stroke="#8b5cf6"
              name="New users"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="clicks"
              stroke="#ec4899"
              name="Clicks"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Dispositivos e Navegadores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Monitor className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900">
              Devices
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={deviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${((percent as any) * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {deviceData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Globe2 className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900">
              Browsers
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dashboard.client_info.browsers}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="browser" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top URLs */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <TrendingUp className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-slate-900">
            Most Popular URLs
          </h3>
        </div>
        <div className="space-y-3">
          {dashboard.top_urls.map((url, index) => (
            <div
              key={url.short_code}
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="flex items-center justify-center w-8 h-8 bg-indigo-100 rounded-full text-indigo-600 font-semibold text-sm">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900">
                    /{url.short_code}
                  </p>
                  <p className="text-sm text-slate-500 truncate">
                    {url.original_url}
                  </p>
                </div>
              </div>
              <div className="text-right ml-4">
                <p className="text-lg font-bold text-slate-900">
                  {url.clicks.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500">clicks</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Geografia e Tags */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Globe className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900">Top Countries</h3>
          </div>
          <div className="space-y-3">
            {dashboard.geography.top_countries.map((country) => (
              <div
                key={country.country_code}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {country.country_code === "US"
                      ? "🇺🇸"
                      : country.country_code === "BR"
                      ? "🇧🇷"
                      : country.country_code === "GB"
                      ? "🇬🇧"
                      : country.country_code === "CA"
                      ? "🇨🇦"
                      : "🇩🇪"}
                  </span>
                  <span className="font-medium text-slate-900">
                    {country.country_code}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32 bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${country.percentage}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-slate-700 w-16 text-right">
                    {country.clicks.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <Tag className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-slate-900">
              Popular Tags
            </h3>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm text-slate-600">Total de Tags</p>
              <p className="text-xl font-bold text-slate-900">
                {dashboard.tags.total_tags}
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm text-slate-600">Average per URL</p>
              <p className="text-xl font-bold text-slate-900">
                {dashboard.tags.avg_tags_per_url.toFixed(1)}
              </p>
            </div>
          </div>
          <div className="space-y-2">
            {dashboard.tags.top_tags.map((tag) => (
              <div
                key={tag.name}
                className="flex items-center justify-between gap-2 p-2 bg-slate-50 rounded-lg"
              >
                <span className="text-sm font-medium text-slate-700 truncate min-w-0">
                  #{tag.name}
                </span>
                <span className="text-sm font-semibold text-indigo-600 flex-shrink-0">
                  {tag.usage_count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sessões */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-slate-900">
            Session Statistics
          </h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <p className="text-2xl font-bold text-slate-900">
              {dashboard.sessions.total}
            </p>
            <p className="text-sm text-slate-600 mt-1">Total</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {dashboard.sessions.active}
            </p>
            <p className="text-sm text-slate-600 mt-1">Active</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {dashboard.sessions.revoked}
            </p>
            <p className="text-sm text-slate-600 mt-1">Revoked</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">
              {dashboard.sessions.users_with_sessions}
            </p>
            <p className="text-sm text-slate-600 mt-1">Users</p>
          </div>
        </div>
      </div>
      {AlertRenderer}
    </div>
  );
}
