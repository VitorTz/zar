import React, { useState } from 'react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { formatApiTimestamp } from '../utils/dateFormatter';
import { UrlStats } from '../model/UrlStats';


const BreakdownList = ({ title, data }: {title: string, data: Record<any, any>}) => {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  return (
    <div className="breakdown-list">
      <h4>{title}</h4>
      <ul>
        {entries.map(([key, value]) => (
          <li key={key}>
            <span>{key}</span>
            <strong>{value as any}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
};


const UrlStatsDisplay = ({ stats }: { stats: UrlStats }) => (
  <div className="stats-display-container">    
    <div className="stats-grid main-metrics">
      <div className="stat-item"><span>Cliques Totais</span><strong>{stats.total_clicks}</strong></div>
      <div className="stat-item"><span>Visitantes Únicos</span><strong>{stats.unique_visitors}</strong></div>
      {stats.first_click && <div className="stat-item"><span>Primeiro Clique</span><strong>{formatApiTimestamp(stats.first_click)}</strong></div>}
      {stats.last_click && <div className="stat-item"><span>Último Clique</span><strong>{formatApiTimestamp(stats.last_click)}</strong></div>}
    </div>
    
    {stats.timeline && stats.timeline.length > 0 && (
      <div className="timeline-chart-wrapper">
        <h4>Cliques por Dia</h4>
        <div className="timeline-chart">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.timeline} margin={{ top: 5, right: 20, left: 0, bottom: 25 }}>
              <XAxis 
                dataKey="day" 
                tickFormatter={(date) => new Date(date + 'T00:00:00').toLocaleString('pt-BR', { day: '2-digit', month: '2-digit' })}
                angle={-45}
                textAnchor="end"
                height={50}
                interval={0}
              />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="clicks" name="Cliques" fill="var(--primary-color)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )}

    <div className="detailed-breakdown">
      <BreakdownList title="Dispositivos" data={stats.devices} />
      <BreakdownList title="Navegadores" data={stats.browsers} />
      <BreakdownList title="Sistemas Operacionais" data={stats.operating_systems} />
    </div>
  </div>
);


const UrlListItem = ({ url, handleDelete, handleFavorite, openModal, handleCopy }: any) => {
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [statsData, setStatsData] = useState(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  const handleToggleStats = async () => {
    if (isStatsOpen) {
      setIsStatsOpen(false);
      return;
    }

    setIsStatsOpen(true);    
    setIsLoadingStats(true);
    try {
      const response = await api.get(
        `/url/${url.short_code}/stats`, {
            headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': '0',
          },
        }
      );
      setStatsData(response.data);
    } catch (error) {
      toast.error("Não foi possível carregar as estatísticas.");
      console.error("Erro ao buscar stats da URL:", error);
      setIsStatsOpen(false);
    } finally {
      setIsLoadingStats(false);
    }
  };

  return (
    <li className={`url-item ${isStatsOpen ? 'stats-open' : ''}`}>
      <div className="url-main-content">
        <div className="qr-code-container">
          <img src={url.qrcode_url} alt={`QR Code for ${url.original_url}`} crossOrigin="anonymous" />
        </div>
        <div className="url-details">
          <div className="url-info">
            <p className="original-url" title={url.original_url}>{url.original_url}</p>
            <a href={url.short_url} target="_blank" rel="noopener noreferrer" className="short-url">{url.short_url}</a>
          </div>
          <div className="url-actions">
            <button className={`icon-button stats-button ${isStatsOpen ? 'active' : ''}`} title="Ver estatísticas" onClick={handleToggleStats}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10M12 20V4M6 20V14"/></svg>
            </button>
            <button className={`icon-button favorite-button ${url.is_favorite ? 'favorited' : ''}`} title={url.is_favorite ? 'Remover dos favoritos' : 'Adicionar aos favoritos'} onClick={() => handleFavorite(url)}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            </button>
            <button className="icon-button download-button" title="Baixar Imagem do QR Code" onClick={() => openModal(url)}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </button>
            <button className="delete-button" onClick={() => handleDelete(url)}>Deletar</button>
            <button onClick={() => handleCopy(url.short_url)}>Copiar</button>
          </div>
        </div>
      </div>
      
      <div className="url-stats-details">
        {isLoadingStats && <p style={{ textAlign: 'center' }}>Carregando estatísticas...</p>}
        {statsData && <UrlStatsDisplay stats={statsData} />}
        <button className="close-stats-button" onClick={() => setIsStatsOpen(false)}>Fechar Estatísticas</button>
      </div>
    </li>
  );
};

export default UrlListItem;