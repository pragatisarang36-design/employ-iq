import { Link, Outlet } from "react-router-dom";
import { BrainCircuit } from "lucide-react";

export function AppLayout() {
  return <div className="min-h-screen"><header className="border-b bg-white"><div className="mx-auto flex max-w-6xl items-center gap-2 px-6 py-4"><BrainCircuit className="h-6 w-6 text-indigo-600" /><Link to="/" className="font-semibold text-slate-900">EmployIQ</Link></div></header><main className="mx-auto max-w-6xl px-6 py-12"><Outlet /></main></div>;
}
