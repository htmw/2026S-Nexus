import React, { useEffect, useState } from "react";
import "./ErrorNotifications.css";
import {
  dismissErrorNotification,
  subscribeToErrorNotifications,
} from "../services/errorNotifications";

function ErrorNotificationCard({ notification }) {
  return (
    <article className="err-card" role="alert">
      <div className="err-card__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
          <path
            d="M12 7.4v5.6M12 16.6h.01"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className="err-card__body">
        <div className="err-card__title">{notification.title}</div>
        <p className="err-card__message">{notification.message}</p>

        {notification.requestId ? (
          <div className="err-card__meta">Request ID: {notification.requestId}</div>
        ) : null}
      </div>

      <button
        type="button"
        className="err-card__dismiss"
        onClick={() => dismissErrorNotification(notification.id)}
        aria-label="Dismiss error notification"
      >
        ×
      </button>
    </article>
  );
}

export default function ErrorNotifications() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    return subscribeToErrorNotifications(setNotifications);
  }, []);

  if (!notifications.length) {
    return null;
  }

  return (
    <section className="err-stack" aria-live="assertive" aria-label="Error notifications">
      {notifications.map((notification) => (
        <ErrorNotificationCard key={notification.id} notification={notification} />
      ))}
    </section>
  );
}
