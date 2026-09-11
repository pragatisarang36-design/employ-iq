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
/**
 * Surfaces the API's per-field `details` rather than the generic
 * "Invalid input data." wrapper, and separates a failed round-trip (CORS,
 * offline, cold start) from a real validation response.
 */
export function errorMessage(error: unknown) {
  const axiosError = error as AxiosError<ApiError>;
  const response = axiosError?.response;
  if (!response) {
    return axiosError?.code === "ECONNABORTED"
      ? "The API took too long to respond. It may be waking up — try again in a moment."
      : "Cannot reach the EmployIQ API. Check your connection, then try again.";
  }
  const details = response.data?.details;
  if (details && typeof details === "object") {
    const parts = Object.entries(details).map(([field, value]) => {
      const text = Array.isArray(value) ? value.join(" ") : String(value);
      return field === "non_field_errors" || field === "detail" ? text : `${field.replaceAll("_", " ")}: ${text}`;
    });
    if (parts.length) return parts.join(" · ");
  }
  return response.data?.message ?? "Unable to complete that request. Please try again.";
}
export type HealthStatus = { status: string; service: string };
export const getHealth = async () => (await api.get<HealthStatus>("/health/")).data;
