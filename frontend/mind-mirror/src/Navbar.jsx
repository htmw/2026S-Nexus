import React from "react";
import "./Navbar.css";
import logo from "./assets/logo3.png";

export default function Navbar({
  username = "User",
  onNavigate = () => {},
  onToggleTheme = () => {},
  onLogout = () => {},
  logoSrc = "",
}) {
  const tabs = ["Journal", "Insights", "Past Entries"];

  return (
    <header className="mm-navbar">
      <div className="mm-navbar__inner">
        {/* Left: Brand */}
        <div className="mm-brand">
          <button
            className="mm-brand__clickable"
            type="button"
            onClick={() => console.log("Home clicked")}
          >
            <img
              src={logo}
              alt="Mind Mirror logo"
              className="mm-brand__logoImg"
            />
            <span className="mm-brand__name">Mind Mirror</span>
          </button>
        </div>

        {/* Center: Tabs */}
        <nav className="mm-tabs" aria-label="Primary">
          {tabs.map((t) => (
            <button
              key={t}
              className="mm-tab"
              onClick={() => onNavigate(t)}
              type="button"
            >
              {t}
            </button>
          ))}
        </nav>

        {/* Right */}
        <div className="mm-actions">
          <div className="mm-userpill">{username}</div>

          <button
            className="mm-iconbtn"
            onClick={onToggleTheme}
            type="button"
            aria-label="Toggle theme"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M21 14.5C19.7 15.1 18.2 15.5 16.6 15.5C11.5 15.5 7.5 11.5 7.5 6.4C7.5 4.8 7.9 3.3 8.5 2C5.3 3.3 3 6.4 3 10.1C3 15 7 19 11.9 19C15.6 19 18.7 16.7 21 14.5Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          <button className="mm-logout" onClick={onLogout} type="button">
            Logout
          </button>
        </div>
      </div>

      <div className="mm-navbar__dividerWrapper">
    <div className="mm-navbar__divider" />
  </div>
    </header>
  );
}