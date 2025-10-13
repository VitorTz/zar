import React, { useState } from 'react';
import './UrlList.css';
import ImageGeneratorModal from './ImageGeneratorModal'; 
import UrlListItem from './UrlListItem';
import toast from 'react-hot-toast';
import { Url } from '../model/Url';
import { useUrlListState } from '../store/urlStore';

interface URLListProps {
  showNoUrlsText?: boolean 
  handleDelete: (url: Url) => any
  handleFavorite: (url: Url) => any
}

const URLList = ({ 
  showNoUrlsText = false, 
  handleDelete, 
  handleFavorite 
}: URLListProps) => {
  const { urlList } = useUrlListState()
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const urls = urlList.getUrls()
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
          {currentUrls.map((url: Url) => (
            <UrlListItem
              key={url.short_code}
              url={url}
              handleDelete={handleDelete}
              handleFavorite={handleFavorite}
              openModal={openModal}
              handleCopy={handleCopy}
            />
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