import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const SignupPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
        setError('A senha deve ter pelo menos 6 caracteres.');
        return;
    }
    try {
      await signup(email, password);
      alert('Conta criada com sucesso! Por favor, faça o login.');
      navigate('/login');
    } catch (err) {
      setError('Falha ao criar conta. O email pode já estar em uso.');
    }
  };

  return (
    <div className="container auth-container">
      <h2>Criar Conta</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Senha" required />
        <button type="submit">Cadastrar</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default SignupPage;