import React, { useState, useEffect } from 'react';
import URLShortenerForm from '../components/URLShortenerForm';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';


const HomePage = () => {
  const [localUrls, setLocalUrls] = useState([]);
  
  useEffect(() => {
    const storedUrls = JSON.parse(localStorage.getItem('localUrls') || '[]');
    setLocalUrls(storedUrls);
  }, []);

  const handleShorten = (newUrl) => {
    if (localUrls.map(i => i.id).includes(newUrl.id)) { return }
    const updatedUrls = [newUrl, ...localUrls];
    setLocalUrls(updatedUrls);
    localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
  };

  const handleDelete = async (url) => {
    const updatedUrls = localUrls.filter(i => i.id != url.id)
    setLocalUrls(updatedUrls)
    localStorage.setItem('localUrls', JSON.stringify(updatedUrls));
    toast.success('URL deletada!');

    try {
      await api.delete('/user/url', { data: { url_id: url.id } });      
    } catch (error) { }

  }

  return (
    <div className="container">
      <h1>Encurte seus links.</h1>
      <URLShortenerForm onShorten={handleShorten} />
      <URLList title="Histórico" urls={localUrls} handleDelete={handleDelete} />
    </div>
  );
};

export default HomePage;