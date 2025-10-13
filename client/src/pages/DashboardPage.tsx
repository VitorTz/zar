import React, { useState, useEffect } from 'react';
import api from '../services/api';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { Url } from '../model/Url';
import { useUrlListState } from '../store/urlStore';

const DashboardPage = () => {
  
  const { user } = useAuth()
  const { urlList, setUrlList} = useUrlListState()
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserUrls = async () => {
      try {
        const response = await api.get('/user/urls');
        setUrlList(urlList.addMany(response.data.results))
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
      setUrlList(urlList.remove(url))
      toast.success('URL deletada!');
      if (user) {      
        api.delete('/user/url', { data: { url_id: url.short_code } });
      }
    } catch (error) {
      setUrlList(urlList.add(url))
      console.error("Falha ao deletar URLs do usuário", error);
    } finally {
      setLoading(false);
    }
  }

  const handleFavorite = async (url: Url) => {    
    const is_favorite = !url.is_favorite
    if (!user) {
      toast.error("Você precisa estar logado para favoritar uma url!")
      return
    }
    setUrlList(urlList.favorite(url, is_favorite))
    if (user) {
      try {
        await api.put('/user/url/favorite', { short_code: url.short_code, is_favorite: !url.is_favorite });
      } catch (error) {
        toast.error("Não foi possível favoritar a url.");
        setUrlList(urlList.favorite(url, !is_favorite))
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
        handleFavorite={handleFavorite}
        handleDelete={handleDeleteUrl} />
    </div>
  );
};

export default DashboardPage;