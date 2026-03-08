import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

export const checkinAPI = {
  create: (data) => api.post("/checkin", data),
};

export default api;