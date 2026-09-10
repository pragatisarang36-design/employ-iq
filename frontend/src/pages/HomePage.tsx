import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";

export function HomePage() {
  const health = useQuery({ queryKey: ["api-health"], queryFn: getHealth, retry: false });
  return <section className="space-y-4"><p className="text-sm font-medium text-indigo-600">Phase 1 foundation</p><h1 className="text-4xl font-bold tracking-tight">EmployIQ</h1><p className="max-w-xl text-slate-600">The application shell is ready. Product workflows will be introduced in subsequent approved phases.</p><p className="rounded-md border bg-white p-4 text-sm">API status: {health.isLoading ? "checking…" : health.isSuccess ? "connected" : "unavailable"}</p></section>;
}
