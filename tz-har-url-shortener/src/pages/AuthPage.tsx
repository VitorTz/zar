import { useState } from "react";
import LoginPage from "./LoginPage";
import SignupPage from "./SignupPage";


const AuthPage = () => {
  const [isLoginView, setIsLoginView] = useState(true);
  return (
    <div className="auth-page">
      <div className="auth-container">
        {isLoginView ? <LoginPage /> : <SignupPage />}
        <button className="auth-toggle-btn" onClick={() => setIsLoginView(!isLoginView)}>
          {isLoginView ? 'Não tem uma conta? Cadastre-se' : 'Já tem uma conta? Faça login'}
        </button>
      </div>
    </div>
  );
};


export default AuthPage