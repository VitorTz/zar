import React, { useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';


const URLShortenerForm = ({ onShorten }: {onShorten: (data: any) => any}) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.post('/url', { url });
      onShorten(response.data);
      setUrl('');
    } catch (err) {
      toast.error('Falha ao encurtar a URL. Verifique se é uma URL válida.')
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit}>
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
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default URLShortenerForm;