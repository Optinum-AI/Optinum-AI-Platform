import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { post, get } from "../api/client";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>(null as unknown as AuthState);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      if (localStorage.getItem("optimum_token")) {
        try {
          setUser(await get<User>("/auth/me"));
        } catch {
          localStorage.removeItem("optimum_token");
        }
      }
      setReady(true);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await post<{ token: string; user: User }>("/auth/login", { email, password });
    localStorage.setItem("optimum_token", res.token);
    setUser(res.user);
  };

  const signup = async (email: string, password: string, full_name: string) => {
    const res = await post<{ token: string; user: User }>("/auth/signup", { email, password, full_name });
    localStorage.setItem("optimum_token", res.token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem("optimum_token");
    setUser(null);
  };

  const refresh = async () => {
    setUser(await get<User>("/auth/me"));
  };

  return (
    <AuthContext.Provider value={{ user, ready, login, signup, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
