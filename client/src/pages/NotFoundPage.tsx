import { Link } from 'react-router-dom';
import './NotFoundPage.css';


const NotFoundPage = () => {
  return (
    <div className="not-found-container">
      <h1>404</h1>
      <h2>Página não encontrada</h2>
      <p>Desculpe, a página que você está procurando não existe ou foi movida.</p>
      <Link to="/" className="back-home-link">
        Voltar para a página inicial
      </Link>
    </div>
  );
};

export default NotFoundPage;