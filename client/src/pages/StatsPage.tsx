// src/pages/StatsPage.tsx
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './StatsPage.css';
import { normalizeTimestamp } from '../utils/util';
import { UserStats } from '../model/User';
import { DashboardStats, TopURL } from '../model/DashboardStats';

// Componente para os cartões de estatísticas gerais
const StatCard = ({ title, value }: {title: string, value: string | number}) => (
  <div className="stat-card">
    <span className="stat-title">{title}</span>
    {/* Formata o número para melhor legibilidade */}
    <span className="stat-value">{typeof value === 'number' ? value.toLocaleString('pt-BR') : value}</span>
  </div>
);

// Componente para a tabela de URLs populares
const PopularUrlsTable = ({ urls }: {urls: TopURL[]}) => (
  <div className="stats-section">
    <h2>Popularidade</h2>
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
              {/* O short_url completo não está no modelo, então usamos o short_code */}
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        await api.post("/auth/refresh")
        const [dashRes, userRes] = await Promise.all([
          api.get('/dashboard/stats'),
          user ? api.get('/user/stats') : Promise.resolve({ data: null })
        ]);
        setDashboardStats(dashRes.data);
        setUserStats(userRes.data);
      } catch (error) {
        console.error("Falha ao buscar estatísticas", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  if (loading || !dashboardStats) {
    return <div className="container"><p>Carregando estatísticas...</p></div>;
  }

  return (
    <div className="container stats-container">
      <h1>Estatísticas Gerais</h1>
      <p style={{textAlign: 'center', marginTop: '-2rem', marginBottom: '2rem', color: 'var(--text-secondary-color)'}}>
          Última atualização: {dashboardStats.last_updated_formatted}
      </p>

      {/* Seção dos cartões de destaque */}
      <div className="stats-grid">
        <StatCard title="Total de URLs" value={dashboardStats.total_urls} />
        <StatCard title="Total de Cliques" value={dashboardStats.total_clicks} />
        <StatCard title="Total de Usuários" value={dashboardStats.total_users} />
        <StatCard title="Sessões Ativas" value={dashboardStats.active_sessions} />
      </div>

      <div className="stats-section">
        <h2>Atividade Diária (Últimos 7 dias)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dashboardStats.growth_timeline.slice(0, 7).reverse()}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tickFormatter={(date) => new Date(date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="total_clicks" name="Cliques" fill="var(--primary-color)" />
            <Bar dataKey="new_urls" name="Novas URLs" fill="var(--primary-hover-color)" />
            <Bar dataKey="new_users" name="Novos Usuários" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Seção de Estatísticas de URL */}
      <div className="stats-section">
          <h2>URLs</h2>
          <div className="stats-grid">
              <StatCard title="URLs Criadas (24h)" value={dashboardStats.urls_created_last_24h} />
              <StatCard title="URLs Criadas (7d)" value={dashboardStats.urls_created_last_7d} />
              <StatCard title="URLs com Alias" value={dashboardStats.custom_alias_urls} />
              <StatCard title="URLs Protegidas" value={dashboardStats.protected_urls} />
              <StatCard title="URLs que Expiram" value={dashboardStats.expiring_urls} />
              <StatCard title="Média de Cliques" value={dashboardStats.avg_clicks_per_url.toFixed(2)} />
          </div>
      </div>
      
       {/* Seção de Atividade do Usuário */}
      <div className="stats-section">
          <h2>Usuários</h2>
          <div className="stats-grid user-stats-grid">
              <StatCard title="Novos Usuários (7d)" value={dashboardStats.new_users_last_7d} />
              <StatCard title="Novos Usuários (30d)" value={dashboardStats.new_users_last_30d} />
              <StatCard title="Usuários Ativos (24h)" value={dashboardStats.users_active_last_24h} />
              <StatCard title="Usuários Ativos (7d)" value={dashboardStats.users_active_last_7d} />
              <StatCard title="Usuários Verificados" value={dashboardStats.verified_users} />
          </div>
      </div>

       {/* Seção de Análises Recentes */}
      <div className="stats-section">
          <h2>Análises Recentes</h2>
          <div className="stats-grid">
              <StatCard title="Cliques (1h)" value={dashboardStats.clicks_last_hour} />
              <StatCard title="Cliques (24h)" value={dashboardStats.clicks_last_24h} />
              <StatCard title="Cliques (7d)" value={dashboardStats.clicks_last_7d} />
              <StatCard title="Visitantes Únicos (24h)" value={dashboardStats.unique_visitors_24h} />
              <StatCard title="Visitantes Únicos (7d)" value={dashboardStats.unique_visitors_7d} />
              <StatCard title="Países Alcançados (30d)" value={dashboardStats.countries_reached_30d} />
          </div>
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
      <PopularUrlsTable urls={dashboardStats.top_urls} />
    </div>
  );
};

export default StatsPage;