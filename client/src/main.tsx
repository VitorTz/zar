import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { UserProvider } from './context/AuthContext.tsx'
import { UrlTagProvider } from './context/TagContext.tsx'
import { ViewProvider } from "./context/ViewContext";
import { UrlProvider } from './context/UrlsContext.tsx'


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UserProvider>
      <UrlProvider>
        <UrlTagProvider>
          <ViewProvider>
            <App />
          </ViewProvider>
        </UrlTagProvider>
      </UrlProvider>
    </UserProvider>
  </StrictMode>,
)
