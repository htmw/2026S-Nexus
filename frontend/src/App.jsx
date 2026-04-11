import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./Pages/Navbar";

import Journal from "./Pages/Journal";
import Insights from "./Pages/Insights";
import PastEntries from "./Pages/PastEntries";
import Login from "./Pages/Login";
import Signup from "./Pages/Signup";
import TherapistDashboard from "./Pages/TherapistDashboard";
import PatientDetail from "./Pages/PatientDetail";
import { Toaster } from "react-hot-toast";

import { AuthProvider, useAuth } from "./context/Authcontext";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AppRoutes (){
  const { isAuthenticated } = useAuth();

  return (
      <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      <Toaster/>
      {isAuthenticated && <Navbar />}

      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/journal" replace /> : <Login />}
        />
        <Route
          path="/signup"
          element={isAuthenticated ? <Navigate to="/journal" replace /> : <Signup />}
        />
        <Route path="/" element={<Navigate to="/journal" replace />} />
        <Route
          path="/journal"
          element={<ProtectedRoute><Journal /></ProtectedRoute>}
        />
        <Route
          path="/insights"
          element={<ProtectedRoute><Insights /></ProtectedRoute>}
        />
        <Route
          path="/past-entries"
          element={<ProtectedRoute><PastEntries /></ProtectedRoute>}
        />
        <Route
          path="/therapist"
          element={<ProtectedRoute><TherapistDashboard /></ProtectedRoute>}
        />
        <Route
          path="/therapist/patients/:patientId"
          element={<ProtectedRoute><PatientDetail /></ProtectedRoute>}
        />
        <Route path="*" element={<Navigate to="/journal" replace />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}