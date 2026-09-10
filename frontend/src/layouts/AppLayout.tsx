import { Link, Outlet, useNavigate } from "react-router-dom";
import { BrainCircuit } from "lucide-react";
import { useAuth } from "@/app/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth(); const navigate = useNavigate();
  return <div className="min-h-screen"><header className="border-b bg-white"><div className="mx-auto flex max-w-6xl items-center gap-2 px-6 py-4"><BrainCircuit className="h-6 w-6 text-indigo-600" /><Link to="/" className="font-semibold text-slate-900">EmployIQ</Link><div className="ml-auto flex items-center gap-3 text-sm">{user ? <><span>{user.email}</span><Link className="text-indigo-600" to={user.role === "student" ? "/student" : "/tpo"}>Workspace</Link><button className="text-indigo-600" onClick={() => void logout().then(() => navigate("/login"))}>Sign out</button></> : <><Link className="text-indigo-600" to="/login">Sign in</Link><Link className="text-indigo-600" to="/register">Register</Link></>}</div></div></header><main className="mx-auto max-w-6xl px-6 py-12"><Outlet /></main></div>;
}
