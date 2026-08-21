"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getCurrentUser } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import {
  isAdminUserList,
  isAdminUser,
  type AdminUser,
  type AuthenticatedUser,
} from "@/types/user";


export default function AdminPage() {
  const [currentUser, setCurrentUser] = useState<AuthenticatedUser | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    let isCancelled = false;

    async function loadUsers(): Promise<void> {
      try {
        const authenticatedUser = await getCurrentUser();
        if (authenticatedUser === null) {
          router.replace("/login");
          return;
        }
        if (!authenticatedUser.is_admin) {
          router.replace("/home");
          return;
        }

        const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error("Failed to load admin users");
        }

        const responseData: unknown = await response.json();
        if (!isAdminUserList(responseData)) {
          throw new Error("Invalid admin users response");
        }

        if (!isCancelled) {
          setCurrentUser(authenticatedUser);
          setUsers(responseData);
        }
      } catch {
        if (!isCancelled) {
          setErrorMessage("ユーザー情報を取得できませんでした。");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadUsers();
    return () => {
      isCancelled = true;
    };
  }, [router]);

  async function handleDelete(user: AdminUser): Promise<void> {
    const confirmed = window.confirm(
      `${user.username} を利用停止にします。よろしいですか？`,
    );
    if (!confirmed) {
      return;
    }

    setDeletingUserId(user.id);
    setErrorMessage(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/admin/users/${user.id}`,
        { method: "DELETE", credentials: "include" },
      );
      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      if (response.status === 403) {
        router.replace("/home");
        return;
      }
      if (!response.ok) {
        throw new Error("Failed to delete user");
      }

      const responseData: unknown = await response.json();
      if (
        !isAdminUser(responseData) ||
        responseData.deleted_at === null
      ) {
        throw new Error("Invalid deleted user response");
      }

      setUsers((currentUsers) =>
        currentUsers.map((currentUser) =>
          currentUser.id === responseData.id
            ? { ...currentUser, deleted_at: responseData.deleted_at }
            : currentUser,
        ),
      );
    } catch {
      setErrorMessage("ユーザーを利用停止にできませんでした。");
    } finally {
      setDeletingUserId(null);
    }
  }

  if (isLoading) {
    return (
      <main className="page-shell">
        <section className="content-card loading-card" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true" />
          <p>管理情報を読み込んでいます...</p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="content-card home-card">
        <header className="home-header">
          <div>
            <p className="eyebrow">Administration</p>
            <h1>ユーザー管理</h1>
          </div>
          <Link className="secondary-button" href="/home">戻る</Link>
        </header>

        {errorMessage && (
          <p className="alert alert-error" role="alert">{errorMessage}</p>
        )}

        <ul className="admin-user-list">
          {users.map((user) => {
            const isCurrentAdmin = user.id === currentUser?.id;
            const isDeleted = user.deleted_at !== null;

            return (
              <li className="admin-user-row" key={user.id}>
                <div>
                  <p className="admin-user-name">
                    {user.username}
                    {user.is_admin && <span className="admin-badge">管理者</span>}
                  </p>
                  <p className="admin-user-email">{user.email}</p>
                </div>
                {isDeleted ? (
                  <span className="deleted-badge">利用停止済み</span>
                ) : (
                  <button
                    className="danger-button"
                    type="button"
                    onClick={() => void handleDelete(user)}
                    disabled={isCurrentAdmin || deletingUserId === user.id}
                    title={isCurrentAdmin ? "自分自身は停止できません" : undefined}
                  >
                    {deletingUserId === user.id ? "停止中..." : "利用停止"}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
