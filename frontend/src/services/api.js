import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

export const checkinAPI = {
  create: (data) => api.post("/checkin", data),
  list: () => api.get("/checkins"),
  summary: () => api.get("/sentiment-summary"),
};

export default api;
