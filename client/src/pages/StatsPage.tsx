import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './StatsPage.css';
import { normalizeTimestamp } from '../utils/util';
import { UserSession, UserSessionPagination, UserStats } from '../model/User';
import { DashboardStats, TopURL } from '../model/DashboardStats';



const StatCard = ({ title, value }: {title: string, value: string | number}) => (
  <div className="stat-card">
    <span className="stat-title">{title}</span>
    <span className="stat-value">{typeof value === 'number' ? value.toLocaleString('pt-BR') : value}</span>
  </div>
);



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



const UserSessionsTable = ({ sessions }: { sessions: UserSession[] }) => (
    <div className="stats-section">
        <h2>Suas Sessões Ativas</h2>
        <div className="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Criada em</th>
                        <th>Último Uso</th>
                        <th>Endereço IP</th>
                        <th>Dispositivo/Navegador</th>
                    </tr>
                </thead>
                <tbody>                    
                    {sessions.map(session => (                        
                        <tr key={session.issued_at}>
                            <td>{normalizeTimestamp(session.issued_at)}</td>
                            <td>{normalizeTimestamp(session.last_used_at)}</td>
                            <td>{session.device_ip}</td>
                            <td className="user-agent-cell" title={session.user_agent ?? 'N/A'}>
                                {session.user_agent}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);


const StatsPage = () => {

  const { user, refreshUser } = useAuth();
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [userSessions, setUserSessions] = useState<UserSessionPagination | null>(null);  
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const currentUser = user || await refreshUser();
      
      if (!currentUser) {
          try {
              const dashRes = await api.getDashboardStats();
              setDashboardStats(dashRes);
          } catch (error) {
              console.error("Falha ao buscar estatísticas do dashboard", error);
          } finally {
              setLoading(false);
          }
          return;
      }
      
      try {
        const [dashRes, userRes, userSes] = await Promise.all([
          api.getDashboardStats(),
          api.getUserStats(),
          api.getSessions()
        ]);
        setDashboardStats(dashRes);
        setUserStats(userRes);
        setUserSessions(userSes);
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
            <Bar dataKey="total_clicks" name="Cliques" fill="var(--primary-color)" legendType='square' />
            <Bar dataKey="new_urls" name="Novas URLs" fill="var(--primary-hover-color)" legendType='square' />
            <Bar dataKey="new_users" name="Novos Usuários" fill="#82ca9d" legendType='square' />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Seção de Estatísticas de URL */}
      <div className="stats-section">
          <h2>URLs</h2>
          <div className="stats-grid">
              <StatCard title="URLs Criadas (24h)" value={dashboardStats.urls_created_last_24h} />
              <StatCard title="URLs Criadas (7d)" value={dashboardStats.urls_created_last_7d} />
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
      {userSessions && userSessions.results && userSessions.results.length > 0 && (
          <UserSessionsTable sessions={userSessions.results} />
      )}
    </div>
  );
};

export default StatsPage;