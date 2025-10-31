import { useAuth } from "../context/AuthContext";
import type { Page } from "../types/Page";
import './NavBar.css'

interface NavbarProps {
    currentPage: Page; 
    onNavigate: (page: Page) => void
}


const Navbar = ({ currentPage, onNavigate }: NavbarProps) => {

  const { user, logout } = useAuth();  

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        TzHar
      </div>
      <div className="navbar-links">
        {(['urls', 'dashboard', 'tags', 'sessions'] as Page[]).map(page => (
          <button
            key={page}
            className={`nav-link ${currentPage === page ? 'active' : ''}`}
            onClick={() => onNavigate(page)}
          >
            {page.charAt(0).toUpperCase() + page.slice(1)}
          </button>
        ))}
      </div>
      <div className="navbar-user">
        <span>{user?.email}</span>
        <button className="btn btn-secondary" onClick={logout}>Logout</button>
      </div>
      <div className="navbar-mobile-toggle">
        {/* Adicionar lógica de toggle mobile se necessário */}
        <span></span>
        <span></span>
        <span></span>
      </div>
    </nav>
  );
};


export default Navbar;