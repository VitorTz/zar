import React, { useState, useEffect } from 'react';
import api from '../services/api';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { Url } from '../model/Url';

const DashboardPage = () => {
  
  const { user } = useAuth()
  const [userUrls, setUserUrls] = useState<Url[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserUrls = async () => {
      try {
        const response = await api.get('/user/urls');
        setUserUrls(response.data.results);
      } catch (error) {
        console.error("Falha ao buscar URLs do usuário", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserUrls();
  }, []);

  const handleDeleteUrl = async (url: Url) => {
    try {
      const updatedUrls = userUrls.filter(i => i.id != url.id)
      setUserUrls(updatedUrls)
      localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
      toast.success('URL deletada!');
      if (user) {      
        api.delete('/user/url', { data: { url_id: url.id } });      
      }
    } catch (error) {
      console.error("Falha ao deletar URLs do usuário", error);
    } finally {
      setLoading(false);
    }
  }

  const handleFavoriteToggle = async (clickedUrl: Url) => {    
    const updatedUrls = userUrls.map(url =>
      url.id === clickedUrl.id ? { ...url, is_favorite: !url.is_favorite } : url
    );
    setUserUrls(updatedUrls);
    if (user) {
      try {
        await api.put(`/url/favorite`, {data: { url_id: clickedUrl.id, state: !clickedUrl.is_favorite }});
      } catch (error) {
        toast.error("Não foi possível favoritar a url.");
        setUserUrls(userUrls);
        console.error("Falha ao favoritar:", error);
      }
    }
  };

  if (loading) {
    return <div className="container"><p>Carregando seu histórico...</p></div>;
  }

  return (
    <div className="container">
      <URLList 
        showNoUrlsText={true} 
        urls={userUrls} 
        handleFavorite={handleFavoriteToggle}
        handleDelete={handleDeleteUrl} />
    </div>
  );
};

export default DashboardPage;