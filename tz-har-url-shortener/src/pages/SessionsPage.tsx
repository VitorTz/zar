import { useState, useEffect } from "react";
import { TzHarAPIError } from "../services/TzHarAPIError";
import type { UserSession } from "../types/user";
import { api } from "../services/TzHarApi";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "../components/LoadingSpinner";


const SessionsPage: React.FC = () => {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { showNotification, logout } = useAuth();
  
  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const data = await api.auth.getSessions();
      setSessions(data.results);
    } catch (error) {
      const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao carregar sessões';
      showNotification(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);
  
  const handleLogoutAll = async () => {
    if (window.confirm('Tem certeza que deseja deslogar de todos os dispositivos? Você será deslogado daqui também.')) {
      try {
        await api.auth.logoutAll();
        showNotification('Sessões encerradas!', 'success');
        logout(); // Desloga o usuário atual
      } catch (error) {
        const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao encerrar sessões';
        showNotification(msg, 'error');
      }
    }
  };
  
  // TODO: A API não parece ter um endpoint para revogar uma *única* sessão.
  // Se tivesse, adicionaríamos um botão "Revogar" em cada item.

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Sessões Ativas</h1>
        <button className="btn btn-danger" onClick={handleLogoutAll}>Deslogar de Todos</button>
      </div>

      {isLoading ? <LoadingSpinner /> : (
        <div className="session-list-container">
          {sessions.length === 0 ? <p>Nenhuma sessão ativa encontrada.</p> : (
            <table className="url-table">
              <thead>
                <tr>
                  <th>Dispositivo</th>
                  <th>IP</th>
                  <th>Último Uso</th>
                  <th>Expira em</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(session => (
                  <tr key={session.issued_at} className={session.revoked ? 'revoked' : ''}>
                    <td data-label="Dispositivo">
                      {session.device_name || session.user_agent?.substring(0, 40) || 'Desconhecido'}
                      {session.revoked && <strong> (Revogada)</strong>}
                    </td>
                    <td data-label="IP">{session.device_ip}</td>
                    <td data-label="Último Uso">{new Date(session.last_used_at).toLocaleString()}</td>
                    <td data-label="Expira em">{new Date(session.expires_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};


export default SessionsPage;