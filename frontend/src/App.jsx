import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Navbar from "./Pages/Navbar";

import Journal from "./Pages/Journal";
import Insights from "./Pages/Insights";
import PastEntries from "./Pages/PastEntries";
import Login from "./Pages/Login";
import Signup from "./Pages/Signup";
import { Toaster } from "react-hot-toast";

export default function App() {

  const location = useLocation();
  const hideNavbarRoutes = ["/login", "/signup"];
  const shouldHideNavbar = hideNavbarRoutes.includes(location.pathname);

  return (
      <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      {!shouldHideNavbar && <Navbar />}
      <Toaster/>

      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/past-entries" element={<PastEntries />} />
        

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}