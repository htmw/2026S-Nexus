import assert from "node:assert/strict";
import test from "node:test";

import { normalizeApiError } from "./apiErrors.js";

test("normalizeApiError uses backend error payload when present", () => {
  const error = {
    response: {
      status: 500,
      data: {
        error: {
          code: "internal_server_error",
          message: "Something went wrong. Please try again.",
          request_id: "req-123",
        },
      },
    },
  };

  const normalizedError = normalizeApiError(error);

  assert.equal(normalizedError.name, "ApiError");
  assert.equal(normalizedError.message, "Something went wrong. Please try again.");
  assert.equal(normalizedError.status, 500);
  assert.equal(normalizedError.code, "internal_server_error");
  assert.equal(normalizedError.requestId, "req-123");
});

test("normalizeApiError falls back to a network message when no response exists", () => {
  const error = {
    request: {},
  };

  const normalizedError = normalizeApiError(error);

  assert.equal(
    normalizedError.message,
    "We couldn't reach the server. Check your connection and try again."
  );
  assert.equal(normalizedError.status, null);
  assert.equal(normalizedError.requestId, "");
});
