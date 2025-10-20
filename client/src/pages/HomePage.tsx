import URLShortenerForm from '../components/URLShortenerForm';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import { api } from '../services/api';
import { URLResponse } from '../model/Url';
import { useAuth } from '../context/AuthContext';
import { useHomePageUrlList } from '../store/homePageUrlList';
import { useEffect } from 'react';


const HomePage = () => {
  
  const { user, refreshUser } = useAuth()
  const { urlList, setUrlList } = useHomePageUrlList()

  useEffect(() => {
    const init = async () => {
      if (!user) {
        refreshUser()     
      }
      init()
    }
  }, [])

  const handleShorten = (url: URLResponse) => {
    setUrlList(urlList.add(url))
  };

  const handleDelete = async (url: URLResponse) => {
    setUrlList(urlList.remove(url))
    toast.success('URL deletada!');
    try {
      await api.deleteUserUrl(url.short_code)      
    } catch (error) { 
      setUrlList(urlList.add(url))
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

  return (
    <div className="container">
      <h1>Encurte seus links.</h1>
      <URLShortenerForm onShorten={handleShorten} />
      <URLList 
        urlList={urlList} 
        handleFavorite={handleFavorite} 
        handleDelete={handleDelete} />
    </div>
  );
};

export default HomePage;