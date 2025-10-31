import { useState, useRef, useEffect, type FormEvent } from "react";
import type { URLResponse, UrlTag, UrlStats } from "../types/URL";
import { TzHarAPIError } from "../services/TzHarAPIError";
import { useAuth } from "../context/AuthContext";
import Modal from "../components/Modal";
import { api } from "../services/TzHarApi";
import LoadingSpinner from "../components/LoadingSpinner";


const UrlsPage = () => {
  const [urls, setUrls] = useState<URLResponse[]>([]);
  const [tags, setTags] = useState<UrlTag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'stats' | 'tags' | null>(null);
  
  const [selectedUrl, setSelectedUrl] = useState<URLResponse | null>(null);
  const [selectedUrlStats, setSelectedUrlStats] = useState<UrlStats | null>(null);
  const [selectedUrlTags, setSelectedUrlTags] = useState<UrlTag[]>([]);

  const { showNotification } = useAuth();
  const shortenUrlInputRef = useRef<HTMLInputElement>(null);

  const fetchUrls = async () => {
    setIsLoading(true);
    try {
      const [urlsData, tagsData] = await Promise.all([
        api.url.getUserUrls(),
        api.tag.getUserTags()
      ]);
      setUrls(urlsData.results);
      setTags(tagsData.results);
    } catch (error) {
      const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao carregar URLs ou Tags';
      showNotification(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUrls();
  }, []);

  const handleShorten = async (e: FormEvent) => {
    e.preventDefault();
    const url = shortenUrlInputRef.current?.value;
    if (!url) {
      showNotification('Por favor, insira uma URL.', 'error');
      return;
    }
    
    try {
      const newUrl = await api.url.shortenUrl({ url });
      setUrls([newUrl, ...urls]);
      showNotification('URL encurtada com sucesso!', 'success');
      if(shortenUrlInputRef.current) {
        shortenUrlInputRef.current.value = '';
      }
    } catch (error) {
       const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao encurtar URL';
       showNotification(msg, 'error');
    }
  };
  
  const handleDelete = async (id: number) => {
    if (window.confirm('Tem certeza que deseja deletar esta URL?')) {
      try {
        await api.url.deleteUserUrl(id);
        setUrls(urls.filter(url => url.id !== id));
        showNotification('URL deletada.', 'success');
      } catch (error) {
        const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao deletar URL';
        showNotification(msg, 'error');
      }
    }
  };

  const handleToggleFavorite = async (url: URLResponse) => {
    try {
      const newIsFavorite = !url.is_favorite;
      await api.url.setFavoriteUrl(url.id, newIsFavorite);
      setUrls(urls.map(u => u.id === url.id ? { ...u, is_favorite: newIsFavorite } : u));
    } catch (error) {
      const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao atualizar favorito';
      showNotification(msg, 'error');
    }
  };
  
  const handleShowStats = async (url: URLResponse) => {
    setSelectedUrl(url);
    setIsModalOpen(true);
    setModalType('stats');
    setSelectedUrlStats(null); // Limpa stats antigos
    try {
      const stats = await api.url.getUrlStats(url.short_code);
      setSelectedUrlStats(stats);
    } catch (error) {
      const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao buscar estatísticas';
      showNotification(msg, 'error');
      // Não fecha o modal, mas o modal deve tratar 'selectedUrlStats' nulo
    }
  };
  
  // TODO: A API não parece ter um endpoint para "buscar tags de uma URL"
  // Vou simular, mas o ideal seria ter `apiClient.getTagsForUrl(url.id)`
  const handleManageTags = (url: URLResponse) => {
     setSelectedUrl(url);
     setModalType('tags');
     // Aqui, você precisaria buscar as tags *já associadas* a esta URL.
     // Como não temos esse endpoint, vamos mostrar todas as tags.
     setSelectedUrlTags([]); // Simulação
     setIsModalOpen(true);
  };
  
  const handleCopy = (shortUrl: string) => {
    // navigator.clipboard.writeText(shortUrl) não funciona em todos os contextos (ex: iframe)
    // Usando a abordagem legada que é mais robusta em iframes.
    const textArea = document.createElement('textarea');
    textArea.value = shortUrl;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showNotification('URL copiada!', 'success');
    } catch (err) {
      showNotification('Não foi possível copiar.', 'error');
    }
    document.body.removeChild(textArea);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedUrl(null);
    setModalType(null);
  };
  
  const renderModalContent = () => {
    if (modalType === 'stats') {
      return (
        <div>
          {selectedUrlStats ? (
            <>
              <p><strong>Total de Cliques:</strong> {selectedUrlStats.total_clicks}</p>
              <p><strong>Cliques Hoje:</strong> {selectedUrlStats.clicks_today}</p>
              <p><strong>Visitantes Únicos:</strong> {selectedUrlStats.unique_visitors}</p>
              <p><strong>Primeiro Clique:</strong> {selectedUrlStats.first_click ? new Date(selectedUrlStats.first_click).toLocaleString() : 'N/A'}</p>
              <p><strong>Último Clique:</strong> {selectedUrlStats.last_click ? new Date(selectedUrlStats.last_click).toLocaleString() : 'N/A'}</p>
              {/* TODO: Renderizar listas de browsers, os, etc. */}
            </>
          ) : <LoadingSpinner />}
        </div>
      );
    }
    if (modalType === 'tags') {
      return (
        <div>
          <p>Selecione as tags para <strong>{selectedUrl?.title || selectedUrl?.short_code}</strong>:</p>
          <div className="tag-management-list">
            {tags.map(tag => (
              <div key={tag.id} className="tag-management-item">
                <input 
                  type="checkbox" 
                  id={`tag-${tag.id}`}
                  // TODO: Precisaria saber se a tag está associada (selectedUrlTags)
                  // defaultChecked={selectedUrlTags.some(t => t.id === tag.id)}
                  onChange={async (e) => {
                    if (!selectedUrl) return;
                    const isChecked = e.target.checked;
                    const action = isChecked ? api.tag.createUrlTagRelation : api.tag.deleteUrlTagRelation;
                    try {
                      await action(selectedUrl.id, tag.id);
                      showNotification(`Tag ${isChecked ? 'adicionada' : 'removida'}.`, 'success');
                      // TODO: Atualizar 'selectedUrlTags'
                    } catch(err) {
                      showNotification('Erro ao atualizar tag.', 'error');
                      e.target.checked = !isChecked; // Reverte
                    }
                  }}
                />
                <label htmlFor={`tag-${tag.id}`} style={{ borderBottomColor: tag.color }}>{tag.name}</label>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Minhas URLs</h1>
      </div>
      
      <form onSubmit={handleShorten} className="shorten-form">
        <input 
          type="url" 
          placeholder="Cole sua URL longa aqui..." 
          ref={shortenUrlInputRef}
          required 
        />
        <button type="submit" className="btn btn-primary">Encurtar</button>
      </form>
      
      {isLoading ? <LoadingSpinner /> : (
        <div className="url-list-container">
          {urls.length === 0 ? <p>Você ainda não encurtou nenhuma URL.</p> : (
            <table className="url-table">
              <thead>
                <tr>
                  <th>URL</th>
                  <th>Cliques</th>
                  <th>Criada em</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {urls.map(url => (
                  <tr key={url.id}>
                    <td data-label="URL">
                      <strong>{url.title || url.short_url}</strong>
                      <small>{url.original_url}</small>
                    </td>
                    <td data-label="Cliques">{url.clicks}</td>
                    <td data-label="Criada em">{new Date(url.created_at).toLocaleDateString()}</td>
                    <td data-label="Ações">
                      <div className="button-group">
                        <button className="btn-icon" onClick={() => handleCopy(url.short_url)} title="Copiar">📋</button>
                        <button 
                          className={`btn-icon ${url.is_favorite ? 'favorited' : ''}`} 
                          onClick={() => handleToggleFavorite(url)}
                          title="Favoritar"
                        >
                          {url.is_favorite ? '★' : '☆'}
                        </button>
                        <button className="btn-icon" onClick={() => handleShowStats(url)} title="Estatísticas">📊</button>
                        <button className="btn-icon" onClick={() => handleManageTags(url)} title="Tags">🏷️</button>
                        <button className="btn-icon btn-danger" onClick={() => handleDelete(url.id)} title="Deletar">🗑️</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
      
      <Modal 
        isOpen={isModalOpen}
        onClose={closeModal}
        title={modalType === 'stats' ? 'Estatísticas da URL' : 'Gerenciar Tags'}
      >
        {renderModalContent()}
      </Modal>
      
    </div>
  );
};



export default UrlsPage;