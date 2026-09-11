import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "@/app/AuthContext";
import { AppLayout } from "@/layouts/AppLayout";
import { LoginPage, RegisterPage } from "@/pages/AuthPages";
import { StudentPage } from "@/pages/StudentPage";
import { StudentProfilePage } from "@/pages/StudentProfilePage";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { TpoPage } from "@/pages/TpoPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });
function HomeRedirect() { const { user, loading } = useAuth(); if (loading) return <p>Loading…</p>; return <Navigate to={user ? (user.role === "student" ? "/student" : "/tpo") : "/login"} replace />; }
function Protected({ children, roles }: { children: ReactNode; roles: string[] }) { const { user, loading } = useAuth(); if (loading) return <p>Loading…</p>; if (!user) return <Navigate to="/login" replace />; if (!roles.includes(user.role)) return <Navigate to={user.role === "student" ? "/student" : "/tpo"} replace />; return <>{children}</>; }
const router = createBrowserRouter([{ element: <AppLayout />, children: [{ path: "/", element: <HomeRedirect /> }, { path: "/login", element: <LoginPage /> }, { path: "/register", element: <RegisterPage /> }, { path: "/student", element: <Protected roles={["student"]}><StudentPage /></Protected> }, { path: "/student/profile", element: <Protected roles={["student"]}><StudentProfilePage /></Protected> }, { path: "/student/assessment", element: <Protected roles={["student"]}><AssessmentPage /></Protected> }, { path: "/tpo", element: <Protected roles={["tpo", "admin"]}><TpoPage /></Protected> }, { path: "*", element: <NotFoundPage /> }] }]);
export function App() { return <QueryClientProvider client={queryClient}><AuthProvider><RouterProvider router={router} /></AuthProvider></QueryClientProvider>; }
