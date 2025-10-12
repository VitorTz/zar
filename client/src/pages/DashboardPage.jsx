import React, { useState, useEffect } from 'react';
import api from '../services/api';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  
  const [userUrls, setUserUrls] = useState([]);
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

  const handleDeleteUrl = async (url) => {
    try {
      console.log(url)
      const response = await api.delete('/user/url', { data: { url_id: url.id } });
      const updatedUrls = userUrls.filter(i => i.id != url.id)
      setUserUrls(updatedUrls)
      localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
      toast.success('URL deletada!');
    } catch (error) {
      console.error("Falha ao deletar URLs do usuário", error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="container"><p>Carregando seu histórico...</p></div>;
  }

  return (
    <div className="container">
      <URLList showNoUrlsText={true} urls={userUrls} handleDelete={handleDeleteUrl} />
    </div>
  );
};

export default DashboardPage;