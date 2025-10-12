import React, { useState, useEffect } from 'react';
import URLShortenerForm from '../components/URLShortenerForm';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Url } from '../model/Url';
import { useAuth } from '../context/AuthContext';
import { useUrlListState } from '../store/urlStore';


const HomePage = () => {
  
  const { user } = useAuth()
  const { urls, setUrls } = useUrlListState()
  
  useEffect(() => {
    const storedUrls = JSON.parse(localStorage.getItem('localUrls') || '[]');
    setUrls(storedUrls)
  }, []);

  const handleShorten = (newUrl: Url) => {
    const updatedUrls = [newUrl, ...urls.filter(i => i.id != newUrl.id)];
    setUrls(updatedUrls);
    localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
  };

  const handleDelete = async (url: Url) => {
    const updatedUrls = urls.filter(i => i.id != url.id)
    setUrls(updatedUrls)
    localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
    toast.success('URL deletada!');
    try {
      await api.delete('/user/url', { data: { url_id: url.id } });      
    } catch (error) { }
  }

  const handleFavoriteToggle = async (clickedUrl: Url) => {
    setUrls(urls.map(url => url.id === clickedUrl.id ? { ...url, is_favorite: !url.is_favorite } : url));
    if (user) {
      try {
        await api.put(`/url/favorite`, {data: { url_id: clickedUrl.id, state: !clickedUrl.is_favorite }});
      } catch (error) {
        toast.error("Não foi possível favoritar a url.");
        console.error("Falha ao favoritar:", error);
        setUrls(urls.map(url => url.id === clickedUrl.id ? { ...url, is_favorite: !url.is_favorite } : url));
      }
    }
  };

  return (
    <div className="container">
      <h1>Encurte seus links.</h1>
      <URLShortenerForm onShorten={handleShorten} />
      <URLList handleFavorite={handleFavoriteToggle} handleDelete={handleDelete} />
    </div>
  );
};

export default HomePage;