import { createContext, useContext, useState, type ReactNode } from "react";
import type { URLResponse } from "../types/URL";


interface UrlContextType {
  urls: URLResponse[];
  setUrls: (urls: URLResponse[]) => void;
}


const UrlContext = createContext<UrlContextType | undefined>(undefined);

export const UrlProvider = ({ children }: { children: ReactNode }) => {
  const [urls, setUrls] = useState<URLResponse[]>([]);  

  return (
    <UrlContext.Provider value={{ urls, setUrls }}>
      {children}
    </UrlContext.Provider>
  );
};

export const useUrls = (): UrlContextType => {
  const context = useContext(UrlContext);
  if (!context) throw new Error("useUrl must be used within a UrlProvider");
  return context;
};