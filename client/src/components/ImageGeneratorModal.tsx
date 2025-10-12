import React, { useState } from 'react';
import { generateUrlImage } from '../utils/imageGenerator';
import toast from 'react-hot-toast';
import './ImageGeneratorModal.css';
import { Url } from '../model/Url';


const ImageGeneratorModal = ({ url, onClose }: {url: Url | null, onClose: () => any}) => {
  const [title, setTitle] = useState('Leia o QR Code!');
  const [description, setDescription] = useState('Aponte a câmera do seu celular para visitar o link.');
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerateAndDownload = async (e: any) => {
    if (url === null) { 
      toast.error("Nenhuma url selecionada!")
      return 
    }
    e.preventDefault();
    setIsLoading(true);
    try {
      const imageDataUrl = await generateUrlImage({
        qrCodeUrl: url.qr_code_url,
        title,
        description,
        originalUrl: url.original_url,
        shortUrl: url.short_url.replace(/^https?:\/\//, '')
      });
      
      const link = document.createElement('a');
      link.href = imageDataUrl;
      link.download = `${url.short_code}-qrcode.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      onClose();

    } catch (error) {
      console.error("Falha ao gerar a imagem:", error);
      toast.error("Não foi possível gerar a imagem. Verifique o console para mais detalhes.")
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="close-button" onClick={onClose}>&times;</div>
        <h2>Gerar Imagem para Download</h2>
        <form onSubmit={handleGenerateAndDownload}>
          <label htmlFor="title">Título</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Título principal da imagem"
          />

          <label htmlFor="description">Descrição</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Texto de descrição"
            style={{ resize: "none" }}
            rows={3}
          />

          <button type="submit" className="generate-button" disabled={isLoading}>
            {isLoading ? 'Gerando...' : 'Gerar e Baixar'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ImageGeneratorModal;