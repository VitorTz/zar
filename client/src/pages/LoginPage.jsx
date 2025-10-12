import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { threadPool } from '../services/ThreadPool';
import api from '../services/api';


const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const postUrl = async (url) => {
    await api.post('/user/url?url_id=' + url.id);
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);      
      const urls = JSON.parse(localStorage.getItem('localUrls'));
      await threadPool(urls, postUrl)
      navigate('/');
    } catch (err) {
      console.log(err)
      toast.error('Credenciais inválidas. Tente novamente.')
    }
  };

  return (
    <div className="container auth-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Senha" required />
        <button type="submit">Entrar</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default LoginPage;