import { useEffect, useState, useRef, type ReactNode } from "react";
import type { NotificationState, NotificationType } from "../types/notification";
import type { User } from "../types/user";
import { TzHarAPIError } from "../services/TzHarAPIError";
import { api } from "../services/TzHarApi";
import { AuthContext } from "../context/AuthContext";
import NotificationContainer from "./NotificationContainer";


interface AuthProviderProps {
    children: ReactNode
}


const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notifications, setNotifications] = useState<NotificationState[]>([]);
  let notificationIdCounter = useRef(0);

  const showNotification = (message: string, type: NotificationType) => {
    const id = notificationIdCounter.current++;
    setNotifications((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 5000);
  };

  useEffect(() => {
    const checkUser = async () => {
      try {
        const userData = await api.auth.getMe();
        setUser(userData);
      } catch (error) {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    checkUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const userData = await api.auth.login(email, password);
      setUser(userData);
      showNotification('Login realizado com sucesso!', 'success');
    } catch (error) {
      const message = error instanceof TzHarAPIError ? error.message : 'Erro desconhecido no login';
      showNotification(message, 'error');
      throw error; // Re-lança para o formulário de login saber que falhou
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      await api.auth.signup(email, password);
      showNotification('Conta criada com sucesso! Fazendo login...', 'success');
      await login(email, password); // Tenta logar após o cadastro
    } catch (error) {
      const message = error instanceof TzHarAPIError ? error.message : 'Erro desconhecido no cadastro';
      showNotification(message, 'error');
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.auth.logout();
      setUser(null);
      showNotification('Logout realizado com sucesso.', 'info');
    } catch (error) {
      const message = error instanceof TzHarAPIError ? error.message : 'Erro ao fazer logout';
      showNotification(message, 'error');
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout, showNotification }}>
      {children}
      <NotificationContainer notifications={notifications} />
    </AuthContext.Provider>
  );
};


export default AuthProvider;