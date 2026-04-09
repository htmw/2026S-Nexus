import assert from "node:assert/strict";
import test from "node:test";

import {
  dismissErrorNotification,
  pushErrorNotification,
  resetErrorNotifications,
  subscribeToErrorNotifications,
} from "./errorNotifications.js";

test("pushErrorNotification publishes and dismisses notifications", () => {
  resetErrorNotifications();

  const snapshots = [];
  const unsubscribe = subscribeToErrorNotifications((notifications) => {
    snapshots.push(notifications.map((notification) => notification.message));
  });

  const notification = pushErrorNotification({
    title: "Server error",
    message: "The server hit a problem. Please try again in a moment.",
    requestId: "req-456",
  });

  assert.ok(notification);
  assert.deepEqual(snapshots.at(-1), [
    "The server hit a problem. Please try again in a moment.",
  ]);

  dismissErrorNotification(notification.id);
  assert.deepEqual(snapshots.at(-1), []);

  unsubscribe();
  resetErrorNotifications();
});

test("pushErrorNotification ignores duplicate notifications", () => {
  resetErrorNotifications();

  pushErrorNotification({
    title: "Request failed",
    message: "We couldn't complete that request right now.",
    requestId: "req-789",
  });
  const duplicate = pushErrorNotification({
    title: "Request failed",
    message: "We couldn't complete that request right now.",
    requestId: "req-789",
  });

  assert.equal(duplicate, null);

  resetErrorNotifications();
});
