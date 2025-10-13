import React, { useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';
import './URLShortenerForm.css'

const URLShortenerForm = ({ onShorten }: { onShorten: (data: any) => any }) => {
  // Estados para todos os campos do formulário
  const [url, setUrl] = useState('');
  const [password, setPassword] = useState('');
  // Estados separados para data e hora
  const [expiryDate, setExpiryDate] = useState(''); 
  const [expiryTime, setExpiryTime] = useState('23:59');
  const [isFavorite, setIsFavorite] = useState(false);

  // Estados de controle da UI
  const [showOptions, setShowOptions] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload: any = {
      url: url,
      is_favorite: isFavorite
    };

    if (password) {
      payload.password = password;
    }
    
    if (expiryDate && expiryTime) {      
      const combinedDateTime = `${expiryDate}T${expiryTime}`;
      payload.expires_at = new Date(combinedDateTime).toISOString();
    }

    try {
      const response = await api.post('/url', payload);
      onShorten(response.data);
      toast.success('URL encurtada com sucesso!');

      // 4. Limpa todos os campos do formulário após o sucesso
      setUrl('');
      setPassword('');
      setExpiryDate(''); // Limpa o estado da data
      setExpiryTime('23:59'); // Limpa o estado da hora
      setIsFavorite(false);
      setShowOptions(false);

    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.[0]?.msg || 'Falha ao encurtar a URL. Verifique se é uma URL válida.';
      toast.error(errorMessage);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit}>
        {/* Input principal da URL (sem alterações) */}
        <div className="main-input-group">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Cole sua URL longa aqui"
            required
          />
          <button className='button' type="submit" disabled={loading}>
            {loading ? 'Encurtando...' : 'Encurtar'}
          </button>
        </div>

        {/* Botão de opções avançadas (sem alterações) */}
        <div className="advanced-options-toggle" onClick={() => setShowOptions(!showOptions)}>
          Opções Avançadas {showOptions ? '▲' : '▼'}
        </div>

        {showOptions && (
          <div className="advanced-options">
            {/* Input de senha (sem alterações) */}
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
            
            {/* GRUPO DE INPUTS PARA DATA E HORA */}
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
            
            {/* Checkbox de favorito (sem alterações) */}
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