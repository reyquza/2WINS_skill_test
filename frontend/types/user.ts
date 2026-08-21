export type User = {
  id: number;
  username: string;
  created_at: string;
};


export type AuthenticatedUser = User & {
  email: string;
  is_admin: boolean;
};


export type AdminUser = AuthenticatedUser & {
  deleted_at: string | null;
};


function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}


export function isUser(value: unknown): value is User {
  return (
    isRecord(value) &&
    Number.isInteger(value.id) &&
    typeof value.username === "string" &&
    value.username.length > 0 &&
    typeof value.created_at === "string"
  );
}


export function isAuthenticatedUser(
  value: unknown,
): value is AuthenticatedUser {
  if (!isRecord(value)) {
    return false;
  }

  const responseRecord = value;
  return (
    isUser(value) &&
    typeof responseRecord.email === "string" &&
    typeof responseRecord.is_admin === "boolean"
  );
}


export function isAdminUser(value: unknown): value is AdminUser {
  if (!isRecord(value)) {
    return false;
  }

  const responseRecord = value;
  return (
    isAuthenticatedUser(value) &&
    (
      responseRecord.deleted_at === null ||
      typeof responseRecord.deleted_at === "string"
    )
  );
}


export function isUserList(value: unknown): value is User[] {
  return Array.isArray(value) && value.every(isUser);
}


export function isAdminUserList(value: unknown): value is AdminUser[] {
  return Array.isArray(value) && value.every(isAdminUser);
}
