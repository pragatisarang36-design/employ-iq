import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

export type HealthStatus = { status: string; service: string };
export const getHealth = async () => (await api.get<HealthStatus>("/health/")).data;
