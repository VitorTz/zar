import React, { useState } from 'react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import './URLShortenerForm.css'
import { URLCreate, URLResponse } from '../model/Url';


interface URLShortenerFormProps {
  onShorten: (url: URLResponse) => any
}


const URLShortenerForm = ({ onShorten }: URLShortenerFormProps) => {

  const [url, setUrl] = useState('');
  const [password, setPassword] = useState('');
  const [expiryDate, setExpiryDate] = useState(''); 
  const [expiryTime, setExpiryTime] = useState('23:59');
  const [isFavorite, setIsFavorite] = useState(false);  
  const [title, setTitle] = useState<string>('')
  const [showOptions, setShowOptions] = useState(false);
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setUrl('');
    setPassword('');
    setExpiryDate('');
    setExpiryTime('23:59');
    setTitle('')
    setIsFavorite(false);
    setShowOptions(false);
  }

  const createShortenPayload = (): URLCreate => {
    return {
      url: url,
      is_favorite: isFavorite,
      expires_at: expiryDate && expiryTime ? new Date(`${expiryDate}T${expiryTime}`).toISOString() : null,
      password: password.trim() != '' ? password.trim() : null,
      title: title.trim() != '' ? title.trim() : null
    };
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);       

    try {
      const newUrl: URLResponse = await api.shortenUrl(createShortenPayload())
      onShorten(newUrl);
      toast.success('URL encurtada com sucesso!');      
      resetForm()
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.[0]?.msg || 'Falha ao encurtar a URL. Verifique se é uma URL válida.';
      toast.error(errorMessage);
      console.error(err);
    }
    
    setLoading(false);
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit}>
        
        <div className="main-input-group">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Cole sua URL aqui"
            required
          />
          <button className='button' type="submit" disabled={loading}>
            {loading ? 'Encurtando...' : 'Encurtar'}
          </button>
        </div>

        {/* Opções (expires_at, password, is_favorite) */}
        <div className="advanced-options-toggle" onClick={() => setShowOptions(!showOptions)}>
          Opções Avançadas {showOptions ? '▲' : '▼'}
        </div>

        {showOptions && (
          <div className="advanced-options">
            {/* password */}
            <div className="form-group">
              <label htmlFor="password">Proteger com Senha</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Deixe em branco para não usar senha"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Nome personalizado</label>
              <input
                id="alias"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Deixe em branco para não definir nenhum nome personalizado"
              />
            </div>
            
            {/* Data e hora inputs */}
            <div className="form-group">
              <label>Data de Expiração (Opcional)</label>
              <div className="datetime-group">
                <input
                  type="date"
                  value={expiryDate}
                  onChange={(e) => setExpiryDate(e.target.value)}
                />
                <input
                  type="time"
                  value={expiryTime}
                  onChange={(e) => setExpiryTime(e.target.value)}
                />
              </div>
            </div>
                        
            <div className="form-group-checkbox">
              <input
                id="is_favorite"
                type="checkbox"
                checked={isFavorite}
                onChange={(e) => setIsFavorite(e.target.checked)}
              />
              <label htmlFor="is_favorite">Marcar como favorito</label>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default URLShortenerForm;