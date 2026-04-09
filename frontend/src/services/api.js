import axios from "axios";
import { installApiErrorInterceptor } from "./apiErrors.js";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: apiBaseUrl,
});

installApiErrorInterceptor(api);

export const checkinAPI = {
  create: (data) => api.post("/checkin", data),
  list: () => api.get("/checkins"),
  summary: () => api.get("/sentiment-summary"),
};

export default api;
