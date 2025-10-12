import React from 'react';
import './UrlList.css';

// 1. Importe o 'toast' da biblioteca
import toast from 'react-hot-toast';

const URLList = ({ showNoUrlsText = false, urls, handleDelete }) => {

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('URL copiada para a área de transferência!');
  };

  if (!urls || urls.length === 0) {
    return showNoUrlsText ? <p>Você ainda não criou nenhuma url</p> : <></>;
  }

  return (
    <div className="url-list-container">
      <ul className="url-list">
        {urls.map((url) => (
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
                <button className="delete-button" onClick={() => handleDelete(url)}>Deletar</button>
                <button onClick={() => handleCopy(url.short_url)}>Copiar</button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default URLList;