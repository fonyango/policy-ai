const API_URL = import.meta.env.VITE_API_URL;
const TOKEN_KEY = "policy_ai_access_token";

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiRequest(path, options = {}) {
  const token = getAccessToken();

  const headers = {
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    logout();
  }

  return response;
}

async function getErrorMessage(response, fallback) {
  try {
    const error = await response.json();
    return error.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function register(email, password) {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to create account.")
    );
  }

  return response.json();
}

export async function login(email, password) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Invalid email or password.")
    );
  }

  const result = await response.json();

  setAccessToken(result.access_token);

  return result;
}

export async function getCurrentUser() {
  const response = await apiRequest("/auth/me");

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to load user account.")
    );
  }

  return response.json();
}

export async function getDocuments() {
  const response = await apiRequest("/documents");

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to load documents.")
    );
  }

  return response.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiRequest("/documents", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to upload document.")
    );
  }

  return response.json();
}

export async function deleteDocument(documentId) {
  const response = await apiRequest(
    `/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to delete document.")
    );
  }

  return response.json();
}

export async function askQuestion(question, documentId = null, limit = 5) {
  const response = await apiRequest("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      document_id: documentId,
      limit,
    }),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to generate an answer.")
    );
  }

  return response.json();
}