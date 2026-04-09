import { pushErrorNotification } from "./errorNotifications.js";

function toSentence(text, fallback) {
  if (!text || typeof text !== "string") {
    return fallback;
  }

  const trimmed = text.trim();
  return trimmed || fallback;
}

function readBackendError(data) {
  if (data?.error && typeof data.error === "object") {
    return {
      message: data.error.message,
      requestId: data.error.request_id,
      code: data.error.code,
    };
  }

  if (typeof data?.detail === "string") {
    return {
      message: data.detail,
      requestId: data?.request_id || "",
      code: data?.code || "",
    };
  }

  if (typeof data?.message === "string") {
    return {
      message: data.message,
      requestId: data?.request_id || "",
      code: data?.code || "",
    };
  }

  return {
    message: "",
    requestId: "",
    code: "",
  };
}

export function normalizeApiError(error) {
  const status = error?.response?.status ?? null;
  const backendError = readBackendError(error?.response?.data);

  let message = backendError.message;
  if (!message && error?.request && !error?.response) {
    message = "We couldn't reach the server. Check your connection and try again.";
  } else if (!message && status && status >= 500) {
    message = "The server hit a problem. Please try again in a moment.";
  } else if (!message && status === 404) {
    message = "We couldn't find what you were looking for.";
  } else if (!message && status === 422) {
    message = "Some information was invalid. Please review it and try again.";
  } else if (!message) {
    message = "We couldn't complete that request right now.";
  }

  const normalizedError = new Error(
    toSentence(message, "We couldn't complete that request right now.")
  );

  normalizedError.name = "ApiError";
  normalizedError.status = status;
  normalizedError.code = backendError.code || error?.code || "";
  normalizedError.requestId = backendError.requestId || "";
  normalizedError.originalError = error;

  return normalizedError;
}

export function installApiErrorInterceptor(apiClient) {
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      const normalizedError = normalizeApiError(error);

      pushErrorNotification({
        title: normalizedError.status && normalizedError.status >= 500
          ? "Server error"
          : "Request failed",
        message: normalizedError.message,
        requestId: normalizedError.requestId,
        status: normalizedError.status,
      });

      return Promise.reject(normalizedError);
    }
  );
}
