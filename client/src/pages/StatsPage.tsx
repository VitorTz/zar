// src/pages/StatsPage.js
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './StatsPage.css';
import { normalizeTimestamp } from '../utils/util';
import { UserStats } from '../model/User';
import { DashboardStats } from '../model/DashboardStats';
import { PopularUrl } from '../utils/PopularUrl';


// Componente para os cartões de estatísticas gerais
const StatCard = ({ title, value }: {title: string, value: string | number}) => (
  <div className="stat-card">
    <span className="stat-title">{title}</span>
    <span className="stat-value">{value}</span>
  </div>
);

// Componente para a tabela de URLs populares
const PopularUrlsTable = ({ urls }: {urls: PopularUrl[]}) => (
  <div className="stats-section">
    <h2>URLs Mais Populares</h2>
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>URL Curta</th>
            <th>URL Original</th>
            <th>Cliques</th>
          </tr>
        </thead>
        <tbody>
          {urls.map(url => (
            <tr key={url.short_code}>
              <td><a href={url.short_url} target="_blank" rel="noopener noreferrer">{url.short_code}</a></td>
              <td className="original-url-cell" title={url.original_url}>{url.original_url}</td>
              <td>{url.clicks}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const StatsPage = () => {
  const { user } = useAuth();
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [popularUrls, setPopularUrls] = useState<PopularUrl[]>([]);
  const [dailyAnalytics, setDailyAnalytics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashRes, popularRes, dailyRes, userRes] = await Promise.all([
          api.get('/metrics/dashboard'),
          api.get('/metrics/urls/popular'),
          api.get('/metrics/daily'),
          user ? api.get('/metrics/user') : Promise.resolve({ data: null })
        ]);
        setDashboardStats(dashRes.data);
        setPopularUrls(popularRes.data.results);
        setDailyAnalytics(dailyRes.data.results);
        setUserStats(userRes.data);
      } catch (error) {
        console.error("Falha ao buscar estatísticas", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  if (loading) {
    return <div className="container"><p>Carregando estatísticas...</p></div>;
  }

  return (
    <div className="container stats-container">
      <h1>Estatísticas Gerais</h1>

      {/* Seção dos cartões de destaque */}
      {dashboardStats && (
        <div className="stats-grid">
          <StatCard title="Total de URLs" value={dashboardStats.total_urls} />
          <StatCard title="Total de Cliques" value={dashboardStats.total_clicks} />
          <StatCard title="Cliques (24h)" value={dashboardStats.clicks_last_24h} />
          <StatCard title="Total de Usuários" value={dashboardStats.total_users} />
        </div>
      )}

      {/* Seção do Gráfico */}
      <div className="stats-section">
        <h2>Atividade Diária (Últimos 7 dias)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dailyAnalytics.slice(-7)}> {/* Mostra apenas os últimos 7 dias */}
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tickFormatter={(date) => new Date(date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="clicks" name="Cliques" fill="var(--primary-color)" />
            <Bar dataKey="unique_visitors" name="Visitantes Únicos" fill="var(--primary-hover-color)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Seção do usuário (se logado) */}
      {userStats && (
        <div className="stats-section">
            <h2>Suas Estatísticas ({userStats.email})</h2>
            <div className="stats-grid user-stats-grid">
                <StatCard title="Total de URLs Criadas" value={userStats.total_urls} />
                <StatCard title="URLs Favoritas" value={userStats.favorite_urls} />
                <StatCard title="Total de Cliques Recebidos" value={userStats.total_clicks} />
                <StatCard title="Membro Desde" value={normalizeTimestamp(userStats.member_since)} />
            </div>
        </div>
      )}


      {/* Seção das URLs populares */}
      <PopularUrlsTable urls={popularUrls} />
    </div>
  );
};

export default StatsPage;