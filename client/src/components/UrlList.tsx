import React, { useState } from 'react';
import './UrlList.css';
import toast from 'react-hot-toast';
import ImageGeneratorModal from './ImageGeneratorModal';
import { Url } from '../model/Url';
import { useUrlListState } from '../store/urlStore';

interface URLListProps  {
  showNoUrlsText?: boolean
  handleDelete: (url: Url) => any
  handleFavorite: (url: Url) => any
}


const URLList = ({ 
  showNoUrlsText = false,   
  handleDelete, 
  handleFavorite 
}: URLListProps) => {
  
  const [currentPage, setCurrentPage] = useState(1);
  const {urls} = useUrlListState()
  const itemsPerPage = 10;

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentUrls = urls.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(urls.length / itemsPerPage);

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUrl, setSelectedUrl] = useState<Url | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('URL copiada para a área de transferência!');
  };

  const openModal = (url: Url) => {
    setSelectedUrl(url);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedUrl(null);
  };

  if (!urls || urls.length === 0) {
    return showNoUrlsText ? <p>Você ainda não criou nenhuma url</p> : <></>;
  }

  return (
    <>
      <div className="url-list-container">
        <ul className="url-list">
          {currentUrls.map((url) => (
            <li key={url.id || url.short_code} className="url-item">
              <div className="qr-code-container">
                <img src={url.qr_code_url} alt={`QR Code for ${url.original_url}`} crossOrigin="anonymous" />
              </div>
              <div className="url-details">
                <div className="url-info">
                  <p className="original-url" title={url.original_url}>{url.original_url}</p>
                  <a href={url.short_url} target="_blank" rel="noopener noreferrer" className="short-url">
                    {url.short_url}
                  </a>
                </div>
                <div className="url-actions">
                  
                  <button
                    className={`icon-button favorite-button ${url.is_favorite ? 'favorited' : ''}`}
                    title={url.is_favorite ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
                    onClick={() => handleFavorite(url)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                  </button>
                  <button className="icon-button" title="Baixar Imagem do QR Code" onClick={() => openModal(url)}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  </button>
                  <button className="delete-button" onClick={() => handleDelete(url)}>Deletar</button>
                  <button onClick={() => handleCopy(url.short_url)}>Copiar</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {totalPages > 1 && (
          <div className="pagination-controls">
            <button onClick={handlePrevPage} disabled={currentPage === 1}>Anterior</button>
            <span>Página {currentPage} de {totalPages}</span>
            <button onClick={handleNextPage} disabled={currentPage === totalPages}>Próximo</button>
          </div>
        )}
      </div>
      {isModalOpen && <ImageGeneratorModal url={selectedUrl} onClose={closeModal} />}
    </>
  );
};

export default URLList;