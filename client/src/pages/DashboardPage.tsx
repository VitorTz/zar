import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { UrlPagination, URLResponse } from '../model/Url';
import { emptyPagination, extractNextPagination, Pagination } from '../model/Pagination';
import { useDashboardUrlList } from '../store/dashBoardUrlList';


const DashboardPage = () => {
  
  const { user, refreshUser } = useAuth()
  const { urlList, setUrlList } = useDashboardUrlList()
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState<Pagination>(emptyPagination())

  useEffect(() => {
    const fetchUserUrls = async () => {
      try {
        const urlPagination: UrlPagination = await api.getUserUrls(pagination.page)
        setUrlList(urlList.set(urlPagination.results))
        setPagination(extractNextPagination(urlPagination))
      } catch (error) {
        console.error("Falha ao buscar URLs do usuário", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserUrls();
  }, []);

  const handleDeleteUrl = async (url: URLResponse) => {
    try {
      setUrlList(urlList.remove(url))
      toast.success('URL deletada!');
      if (user) { await api.deleteUserUrl(url.short_code) }
    } catch (error) {
      setUrlList(urlList.add(url))
      console.error("Falha ao deletar URLs do usuário", error);
    } finally {
      setLoading(false);
    }
  }

  const handleFavorite = async (url: URLResponse) => {    
    const is_favorite = !url.is_favorite
    const u = user ? user : await refreshUser()
    if (!u) {
      toast.error("Você precisa estar logado para favoritar uma url!")
      return
    }
    setUrlList(urlList.favorite(url, is_favorite))
    try {
      await api.setFavorite(url.short_code, is_favorite)
    } catch (err) {
      toast.error("Não foi possível favoritar a url.");
      setUrlList(urlList.favorite(url, !is_favorite))
      console.error("Falha ao favoritar:", err);
    }
  };

  if (loading) {
    return <div className="container"><p>Carregando seu histórico...</p></div>;
  }

  return (
    <div className="container">
      <URLList 
        urlList={urlList}
        showNoUrlsText={true}
        handleFavorite={handleFavorite}
        handleDelete={handleDeleteUrl} />
    </div>
  );
};

export default DashboardPage;