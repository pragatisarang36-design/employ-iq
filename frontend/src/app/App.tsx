import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });
const router = createBrowserRouter([{ element: <AppLayout />, children: [{ path: "/", element: <HomePage /> }, { path: "*", element: <NotFoundPage /> }] }]);
export function App() { return <QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>; }
