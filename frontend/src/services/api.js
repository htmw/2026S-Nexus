import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

let _token = null;
 
export function setAuthToken(token) {
  _token = token;
}
 
api.interceptors.request.use((config) => {
  if (_token) {
    config.headers.Authorization = `Bearer ${_token}`;
  }
  return config;
});
 
export const authAPI = {
  login:    (data) => api.post("/login",    data),
  register: (data) => api.post("/register", data),
};
export const checkinAPI = {
  create: (data) => api.post("/checkin", data),
  getAll: () => api.get("/checkins"),
};

export default api;