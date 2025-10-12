// src/components/Navbar.js
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleNavigate = (path) => {
    navigate(path);
    setIsMenuOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setIsMenuOpen(false);
  };
  
  const isActive = (path) => location.pathname === path;

  const statsPath = '/stats'; 
  const homePath = '/';
  const dashboardPath = '/dashboard';
  const loginPath = '/login';
  const signupPath = '/signup';

  const navLinksContent = (
    <>
      {user ? (
        <div className="navbar-user-section">
          <button className={`nav-button ${isActive(homePath) ? 'active' : ''}`} onClick={() => handleNavigate(homePath)}> Home </button>
          <button 
            className={`nav-button ${isActive(dashboardPath) ? 'active' : ''}`} 
            onClick={() => handleNavigate(dashboardPath)}
          >
            Dashboard
          </button>          
          
          <button 
            className={`nav-button ${isActive(statsPath) ? 'active' : ''}`} 
            onClick={() => handleNavigate(statsPath)}
          >
            Stats
          </button>
          
          <div className="email-logout-wrapper">
            <span className="navbar-user-email">{user.email}</span>
            <div onClick={handleLogout} className="icon-logout-button" title="Logout">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </div>
          </div>

        </div>
      ) : (
        <>
          <button className={`nav-button ${isActive(homePath) ? 'active' : ''}`} onClick={() => handleNavigate(homePath)}> Home </button>
          <button className={`nav-button ${isActive(statsPath) ? 'active' : ''}`} onClick={() => handleNavigate(statsPath)}>Stats</button>
          <button className={`nav-button ${isActive(loginPath) ? 'active' : ''}`} onClick={() => handleNavigate(loginPath)}>Login</button>
          <button className={`nav-button ${isActive(signupPath) ? 'active' : ''}`} onClick={() => handleNavigate(signupPath)}>Signup</button>
        </>
      )}
    </>
  );

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Zar</Link>
      </div>
      <div className="navbar-links">{navLinksContent}</div>
      <button className="hamburger-menu" onClick={toggleMenu}>
        <span /><span /><span />
      </button>
      <div className={`mobile-menu ${isMenuOpen ? 'open' : ''}`}>{navLinksContent}</div>
    </nav>
  );
};

export default Navbar;