import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "./Signup.css";
import Navbar from "./Navbar";

export default function Signup() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    if (!fullName || !email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    if (!email.includes("@")) {
      setError("Please enter a valid email.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setError("");
    console.log("Signup submitted:", { fullName, email, password });

    navigate("/journal");
  }

  return (
    <>
      <Navbar variant="auth" />

      <main className="signup-page">
        <div className="signup-shell">
          <section className="signup-main">
            <div className="signup-heading">
              <h1 className="signup-heading__title">Sign Up</h1>
              <p className="signup-heading__subtitle">
                Create A New Mind Mirror Account
              </p>
            </div>

            <form className="signup-form" onSubmit={handleSubmit}>
              <div className="signup-fieldGroup">
                <label className="signup-label" htmlFor="fullName">
                  Full Name
                </label>
                <div className="signup-inputWrap">
                  <span className="signup-inputIcon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.8" />
                      <path
                        d="M5.5 18.2C6.6 15.6 9 14.4 12 14.4C15 14.4 17.4 15.6 18.5 18.2"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <rect x="4.2" y="4.2" width="15.6" height="15.6" rx="3.2" opacity="0" />
                    </svg>
                  </span>

                  <input
                    id="fullName"
                    type="text"
                    className="signup-input"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    autoComplete="name"
                  />
                </div>
              </div>

              <div className="signup-fieldGroup">
                <label className="signup-label" htmlFor="email">
                  Email
                </label>
                <div className="signup-inputWrap">
                  <span className="signup-inputIcon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <rect x="3.5" y="5" width="17" height="14" rx="2.5" stroke="currentColor" strokeWidth="1.8" />
                      <path
                        d="M5 7L12 12.5L19 7"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>

                  <input
                    id="email"
                    type="email"
                    className="signup-input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="signup-fieldGroup">
                <label className="signup-label" htmlFor="password">
                  Password
                </label>
                <div className="signup-inputWrap">
                  <span className="signup-inputIcon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <rect x="5.5" y="10" width="13" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" />
                      <path
                        d="M8 10V7.8C8 5.7 9.7 4 11.8 4C13.9 4 15.6 5.7 15.6 7.8V10"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <circle cx="12" cy="15" r="1.2" fill="currentColor" />
                    </svg>
                  </span>

                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    className="signup-input signup-input--password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                  />

                  <button
                    type="button"
                    className="signup-showBtn"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M2.5 12C4.4 8.5 7.7 6.5 12 6.5C16.3 6.5 19.6 8.5 21.5 12C19.6 15.5 16.3 17.5 12 17.5C7.7 17.5 4.4 15.5 2.5 12Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                      />
                      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
                    </svg>
                  </button>
                </div>
              </div>

              {error && <p className="signup-error">{error}</p>}

              <button type="submit" className="signup-submit">
                Sign Up
              </button>

              <p className="signup-loginText">
                Already have an account?{" "}
                <NavLink to="/login" className="signup-link signup-link--strong">
                  Log In
                </NavLink>
              </p>
            </form>
          </section>
        </div>

        <footer className="signup-footer">
          <p className="signup-footer__text">
            By signing up you agree to our{" "}
            <a href="#" className="signup-footer__link">
              Terms of Services
            </a>{" "}
            &{" "}
            <a href="#" className="signup-footer__link">
              Privacy Policy
            </a>
          </p>
        </footer>
      </main>
    </>
  );
}