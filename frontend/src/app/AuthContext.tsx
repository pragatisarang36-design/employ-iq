import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, tokenStore } from "@/lib/api";
import type { User } from "@/lib/types";

type Auth = { user: User | null; loading: boolean; signIn: (email: string, password: string, institution_slug?: string) => Promise<User>; register: (data: Record<string, string>) => Promise<User>; logout: () => Promise<void> };
const AuthContext = createContext<Auth | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true);
  const load = async () => { if (!tokenStore.access) { setLoading(false); return; } try { setUser((await api.get<User>("/v1/me/")).data); } catch { tokenStore.clear(); setUser(null); } finally { setLoading(false); } };
  useEffect(() => { void load(); const clear = () => { tokenStore.clear(); setUser(null); }; window.addEventListener("employiq:logout", clear); return () => window.removeEventListener("employiq:logout", clear); }, []);
  const signIn = async (email: string, password: string, institution_slug?: string) => { const { data } = await api.post<{ access: string; refresh: string }>("/v1/auth/token/", { email, password, ...(institution_slug ? { institution_slug } : {}) }); tokenStore.set(data.access, data.refresh); const current = (await api.get<User>("/v1/me/")).data; setUser(current); return current; };
  const register = async (data: Record<string, string>) => (await api.post<User>("/v1/auth/register/", { ...data, role: "student" })).data;
  const logout = async () => { try { if (localStorage.getItem("employiq_refresh")) await api.post("/v1/auth/logout/", { refresh: localStorage.getItem("employiq_refresh") }); } finally { tokenStore.clear(); setUser(null); } };
  return <AuthContext.Provider value={{ user, loading, signIn, register, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider is required"); return value; };
