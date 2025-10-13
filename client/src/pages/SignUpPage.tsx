import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';


const SignupPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
        toast.error('A senha deve ter pelo menos 6 caracteres.')
        return;
    }
    try {
      await signup(email, password);
      toast.success('Conta criada com sucesso! Por favor, faça o login.')
      navigate('/login');
    } catch (err) {
      toast.error('Falha ao criar conta. O email pode já estar em uso.')
    }
  };

  return (
    <div className="container auth-container">
      <h2>Criar Conta</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />

        <div className="password-input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'} 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder="Senha" 
            required 
          />
                    
          <button 
            type="button"
            className="password-toggle-button"
            onClick={() => setShowPassword(!showPassword)}
            title={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
          >
            {/* Ícone muda com base no estado */}
            {showPassword ? (
              // Ícone de "olho aberto"
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            ) : (
              // Ícone de "olho fechado"
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
            )}
          </button>
        </div>

        <button className='button' type="submit">Cadastrar</button>

      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default SignupPage;