import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
export const api = axios.create({ baseURL, headers: { "Content-Type": "application/json" } });

let accessToken: string | null = localStorage.getItem("employiq_access");
let refreshToken: string | null = localStorage.getItem("employiq_refresh");
let refreshPromise: Promise<string | null> | null = null;
export const tokenStore = {
  get access() { return accessToken; },
  set(access: string, refresh: string) { accessToken = access; refreshToken = refresh; localStorage.setItem("employiq_access", access); localStorage.setItem("employiq_refresh", refresh); },
  clear() { accessToken = null; refreshToken = null; localStorage.removeItem("employiq_access"); localStorage.removeItem("employiq_refresh"); },
};

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});
api.interceptors.response.use(undefined, async (error: AxiosError) => {
  const request = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
  if (error.response?.status !== 401 || !request || request._retried || !refreshToken || request.url?.includes("auth/token")) return Promise.reject(error);
  request._retried = true;
  refreshPromise ??= api.post<{ access: string; refresh?: string }>("/v1/auth/token/refresh/", { refresh: refreshToken })
    .then(({ data }) => { tokenStore.set(data.access, data.refresh ?? refreshToken!); return data.access; })
    .catch(() => { tokenStore.clear(); window.dispatchEvent(new Event("employiq:logout")); return null; })
    .finally(() => { refreshPromise = null; });
  const token = await refreshPromise;
  if (!token) return Promise.reject(error);
  request.headers.Authorization = `Bearer ${token}`;
  return api(request);
});

export type ApiError = { code?: string; message?: string; details?: Record<string, string[] | string> };
export function errorMessage(error: unknown) { const data = (error as AxiosError<ApiError>)?.response?.data; return data?.message ?? "Unable to complete that request. Please try again."; }
export type HealthStatus = { status: string; service: string };
export const getHealth = async () => (await api.get<HealthStatus>("/health/")).data;
