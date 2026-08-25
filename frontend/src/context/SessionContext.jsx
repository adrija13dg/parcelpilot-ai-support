import { createContext, useContext, useState } from 'react';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('pp-session');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (data) => {
    localStorage.setItem('pp-session', JSON.stringify(data));
    setSession(data);
  };

  const logout = () => {
    localStorage.removeItem('pp-session');
    setSession(null);
  };

  return (
    <SessionContext.Provider value={{ session, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => useContext(SessionContext);
