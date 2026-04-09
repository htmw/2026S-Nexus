import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./Pages/Navbar";
import ErrorNotifications from "./components/ErrorNotifications";

import Journal from "./Pages/Journal";
import Insights from "./Pages/Insights";
import PastEntries from "./Pages/PastEntries";
import { Toaster } from "react-hot-toast";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      <Navbar />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            borderRadius: "14px",
            background: "#fffaf6",
            color: "#4d5b64",
            border: "1px solid rgba(108, 143, 198, 0.16)",
            boxShadow: "0 12px 26px rgba(47, 47, 47, 0.08)",
          },
        }}
      />
      <ErrorNotifications />

      <Routes>
        <Route path="/" element={<Navigate to="/journal" replace />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/past-entries" element={<PastEntries />} />
        <Route path="*" element={<Navigate to="/journal" replace />} />
      </Routes>
    </div>
  );
}
