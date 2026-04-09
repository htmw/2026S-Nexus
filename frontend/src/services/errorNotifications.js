const listeners = new Set();

let notifications = [];
let nextNotificationId = 1;

function emitChange() {
  for (const listener of listeners) {
    listener(notifications);
  }
}

function isDuplicateNotification(nextNotification) {
  return notifications.some(
    (notification) =>
      notification.title === nextNotification.title &&
      notification.message === nextNotification.message &&
      notification.requestId === nextNotification.requestId
  );
}

export function pushErrorNotification({
  title = "Something went wrong",
  message,
  requestId = "",
  status = null,
}) {
  const nextNotification = {
    id: nextNotificationId++,
    title,
    message,
    requestId,
    status,
  };

  if (isDuplicateNotification(nextNotification)) {
    return null;
  }

  notifications = [nextNotification, ...notifications].slice(0, 4);
  emitChange();
  return nextNotification;
}

export function dismissErrorNotification(notificationId) {
  notifications = notifications.filter((notification) => notification.id !== notificationId);
  emitChange();
}

export function subscribeToErrorNotifications(listener) {
  listeners.add(listener);
  listener(notifications);

  return () => {
    listeners.delete(listener);
  };
}

export function resetErrorNotifications() {
  notifications = [];
  nextNotificationId = 1;
  emitChange();
}
