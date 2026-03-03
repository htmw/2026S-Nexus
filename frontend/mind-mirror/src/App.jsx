import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./Navbar";

import Journal from "./Pages/Journal";
import Insights from "./Pages/Insights";
import PastEntries from "./Pages/PastEntries";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      <Navbar />

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