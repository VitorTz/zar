import { createContext, useContext, useState, type ReactNode } from "react";
import type { User, UserSession } from "../types/user";


interface UserContextType {
  user: User | null;
  session: UserSession | null;
  setUser: (user: User | null) => void;
  setSession: (session: UserSession | null) => void;
  logout: () => void;
}


const UserContext = createContext<UserContextType | undefined>(undefined);


export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<UserSession | null>(null);

  const logout = () => {
    setUser(null);
    setSession(null);
  };

  return (
    <UserContext.Provider value={{ user, session, setUser, setSession, logout }}>
      {children}
    </UserContext.Provider>
  );
};


export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) throw new Error("useUser must be used within a UserProvider");
  return context;
};