import { createContext, useContext, useState, type ReactNode } from "react";

export type View = "login" | "signup" | "dashboard" | "urls" | "tags" | "db" | "github" | "api";

interface ViewContextType {
  view: View;
  setView: (view: View) => void;
  resetView: () => void;
}

const ViewContext = createContext<ViewContextType | undefined>(undefined);

export const ViewProvider = ({ children }: { children: ReactNode }) => {
  const [view, setView] = useState<View>("login");

  const resetView = () => setView("login");

  return (
    <ViewContext.Provider value={{ view, setView, resetView }}>
      {children}
    </ViewContext.Provider>
  );
};

export const useView = (): ViewContextType => {
  const context = useContext(ViewContext);
  if (!context) throw new Error("useView must be used within a ViewProvider");
  return context;
};