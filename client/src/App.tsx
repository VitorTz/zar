import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignUpPage';
import DashboardPage from './pages/DashboardPage';
import StatsPage from './pages/StatsPage';
import { useAuth } from './context/AuthContext';
import { Toaster } from 'react-hot-toast';
import Footer from './components/Footer';
import NotFoundPage from './pages/NotFoundPage'; // 1. Importe a nova página
import './App.css';


const PrivateRoute = ({ children }: {children: any}) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (    
    <div className="app-container"> 
      <Toaster
        position="top-center"
        reverseOrder={false}
        toastOptions={{
          className: '',
          duration: 3000,
          style: { background: '#363636', color: '#fff' },
          success: { duration: 2000 },
          error: { duration: 3000 },
        }}
      />
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route 
            path="/dashboard"
            element={<PrivateRoute><DashboardPage /></PrivateRoute>} 
          />
          <Route path="/stats" element={<StatsPage />} />          
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
            
      <Footer />
    </div>
  );
}

export default App;