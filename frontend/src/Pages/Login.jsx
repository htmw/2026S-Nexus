import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "./Login.css";
import logo from "../assets/logo3.png";
import Navbar from "./Navbar";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    if (!email || !password) {
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
    console.log("Login submitted:", { email, password, rememberMe });

    navigate("/journal");
  }

  return (
    <> 
    <Navbar variant="auth" />
    <main className="login-page">
      <div className="login-shell">
        <section className="login-main">
          <div className="login-heading">
            <h2 className="login-heading__title">Welcome Back</h2>
            <p className="login-heading__subtitle">Sign in to continue your reflection journey</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="login-fieldGroup">
              <label className="login-label" htmlFor="email">
                Email
              </label>
              <div className="login-inputWrap">
                <span className="login-inputIcon" aria-hidden="true">
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
                  className="login-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="login-fieldGroup">
              <label className="login-label" htmlFor="password">
                Password
              </label>
              <div className="login-inputWrap">
                <span className="login-inputIcon" aria-hidden="true">
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
                  className="login-input login-input--password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  className="login-showBtn"
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

            <div className="login-options">
              <label className="login-remember">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember me</span>
              </label>

              <NavLink to="/forgot-password" className="login-link">
                Forgot Password?
              </NavLink>
            </div>

            {error && <p className="login-error">{error}</p>}

            <button type="submit" className="login-submit">
              Log In
            </button>

            <p className="login-signupText">
              Don&apos;t have an account?{" "}
              <NavLink to="/signup" className="login-link login-link--strong">
                Sign Up
              </NavLink>
            </p>
          </form>
        </section>
      </div>

      <footer className="login-footer">
        <p className="login-footer__text">
          By logging in you agree to our{" "}
          <a href="#" className="login-footer__link">
            Terms of Services
          </a>{" "}
          &{" "}
          <a href="#" className="login-footer__link">
            Privacy Policy
          </a>
        </p>
      </footer>
    </main>
    </>
  );
}