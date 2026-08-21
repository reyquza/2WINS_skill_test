import { API_BASE_URL } from "@/lib/config";
import {
  isAuthenticatedUser,
  type AuthenticatedUser,
} from "@/types/user";


export async function getCurrentUser(): Promise<AuthenticatedUser | null> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load the current user");
  }

  const responseData: unknown = await response.json();
  if (!isAuthenticatedUser(responseData)) {
    throw new Error("Invalid current user response");
  }

  return responseData;
}


export async function logoutCurrentUser(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to log out");
  }
}
