import URLShortenerForm from '../components/URLShortenerForm';
import URLList from '../components/UrlList';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Url } from '../model/Url';
import { useAuth } from '../context/AuthContext';
import { useUrlListState } from '../store/urlStore';


const HomePage = () => {
  
  const { user } = useAuth()
  const { urlList, setUrlList } = useUrlListState()

  const handleShorten = (url: Url) => {
    setUrlList(urlList.add(url))
  };

  const handleDelete = async (url: Url) => {
    setUrlList(urlList.remove(url))
    toast.success('URL deletada!');
    try {
      await api.delete('/user/url', { data: { short_code: url.short_code } });
    } catch (error) { 
      setUrlList(urlList.add(url))
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
        await api.put(`/url/favorite`, {data: { short_code: url.short_code, is_favorite: !url.is_favorite }});
      } catch (error) {
        toast.error("Não foi possível favoritar a url.");
        console.error("Falha ao favoritar:", error);
        setUrlList(urlList.favorite(url, !is_favorite))
      }
    }
  };

  return (
    <div className="container">
      <h1>Encurte seus links.</h1>
      <URLShortenerForm onShorten={handleShorten} />
      <URLList handleFavorite={handleFavorite} handleDelete={handleDelete} />
    </div>
  );
};

export default HomePage;