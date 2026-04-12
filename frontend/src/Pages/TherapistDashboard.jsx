import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { therapistAPI } from "../services/api";

export default function TherapistDashboard() {
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const previousRole = localStorage.getItem("mindmirror:role");
    const previousUserId = localStorage.getItem("mindmirror:userId");

    localStorage.setItem("mindmirror:role", "therapist");
    localStorage.setItem("mindmirror:userId", previousUserId || "therapist-demo-1");

    let mounted = true;
    async function loadPatients() {
      try {
        const response = await therapistAPI.patients();
        if (!mounted) return;
        setPatients(response.data?.patients || []);
      } catch {
        if (!mounted) return;
        setErrorMessage("Unable to load patient list.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    loadPatients();
    return () => {
      mounted = false;
      if (previousRole) {
        localStorage.setItem("mindmirror:role", previousRole);
      } else {
        localStorage.removeItem("mindmirror:role");
      }
      if (previousUserId) {
        localStorage.setItem("mindmirror:userId", previousUserId);
      } else {
        localStorage.removeItem("mindmirror:userId");
      }
    };
  }, []);

  return (
    <main style={{ padding: "24px", maxWidth: "1000px", margin: "0 auto" }}>
      <h2 style={{ marginBottom: "8px" }}>Therapist Dashboard</h2>
      <p style={{ color: "#4b5563" }}>Select a patient to view read-only journal and mood trends.</p>

      {isLoading ? <p>Loading patients…</p> : null}
      {errorMessage ? <p>{errorMessage}</p> : null}

      {!isLoading && !patients.length ? <p>No linked patients found.</p> : null}

      <div style={{ display: "grid", gap: "12px" }}>
        {patients.map((patient) => (
          <div
            key={patient.patient_id}
            style={{
              background: "#fff",
              border: "1px solid #e5e7eb",
              borderRadius: "12px",
              padding: "12px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>{patient.name}</div>
              <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>{patient.email}</div>
            </div>
            <Link to={`/therapist/patients/${patient.patient_id}`}>Open</Link>
          </div>
        ))}
      </div>
    </main>
  );
}
