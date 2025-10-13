import './Footer.css';


const Footer = () => {
  return (
    <footer className="site-footer">
      <div className="footer-content">
        <div className="security-info">
          <p>
            Para garantir a sua segurança, este serviço utiliza a <strong><a target="_blank" href="https://developers.google.com/safe-browsing/v4/" className='footer-link'>Google Safe Browsing API</a></strong>. Todas as URLs são verificadas antes de serem encurtadas para proteger você contra sites maliciosos, phishing e malware.
          </p>
          <p>
            <strong>Por que isso é importante?</strong> Ao bloquear links perigosos, garantimos que nossa plataforma seja um ambiente seguro e confiável para todos os usuários. Sua proteção é nossa prioridade.
          </p>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Zar Shortener. Todos os direitos reservados.</p>
      </div>
    </footer>
  );
};

export default Footer