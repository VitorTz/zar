import { useState, useEffect } from "react";
import type { Dashboard } from "../types/dashboard";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/TzHarApi";
import { TzHarAPIError } from "../services/TzHarAPIError";
import LoadingSpinner from "../components/LoadingSpinner";


const DashboardPage = () => {
  const [data, setData] = useState<Dashboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { showNotification } = useAuth();

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const dashboardData = await api.dashboard.getDashboard();
      setData(dashboardData);
    } catch (error) {
      const message = error instanceof TzHarAPIError ? error.message : 'Erro ao carregar dashboard';
      showNotification(message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading && !data) {
    return <LoadingSpinner />;
  }

  if (!data) {
    return <div className="page-content"><p>Não foi possível carregar os dados do dashboard.</p></div>;
  }

  return (
    <div className="page-content dashboard-page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <button className="btn btn-primary" onClick={() => fetchData()} disabled={isLoading}>
          {isLoading ? 'Atualizando...' : 'Atualizar Dados'}
        </button>
      </div>
      <p>Última atualização: {new Date(data.last_updated).toLocaleString()}</p>
      
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Total de URLs</h3>
          <p>{data.urls?.total ?? 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>Total de Cliques</h3>
          <p>{data.clicks?.total ?? 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>Cliques Hoje</h3>
          <p>{data.clicks?.today ?? 'N/A'}</p>
        </div>
         <div className="stat-card">
          <h3>Total de Usuários</h3>
          <p>{data.users?.total ?? 'N/A'}</p>
        </div>
      </div>
      
      <div className="dashboard-columns">
        <div className="dashboard-column">
          <h2>Top URLs</h2>
          {data.top_urls.length > 0 ? (
            <ul className="data-list">
              {data.top_urls.map((url: any) => (
                <li key={url.id}>
                  <span>{url.title || url.short_code}</span>
                  <strong>{url.clicks} cliques</strong>
                </li>
              ))}
            </ul>
          ) : <p>Nenhuma URL no top.</p>}
        </div>
        
        <div className="dashboard-column">
          <h2>Geografia (Top Países)</h2>
          {data.geography?.countries?.length > 0 ? (
             <ul className="data-list">
              {data.geography.countries.map((geo: any) => (
                <li key={geo.country}>
                  <span>{geo.country || 'Desconhecido'}</span>
                  <strong>{geo.clicks} cliques</strong>
                </li>
              ))}
            </ul>
          ) : <p>Sem dados geográficos.</p>}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;