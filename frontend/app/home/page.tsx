"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import UserList from "@/components/UserList";
import { getCurrentUser, logoutCurrentUser } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/config";
import { isRoom } from "@/types/room";
import {
  isUserList,
  type AuthenticatedUser,
  type User,
} from "@/types/user";


export default function HomePage() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<AuthenticatedUser | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [openingUserId, setOpeningUserId] = useState<number | null>(null);
  const router = useRouter();

  useEffect(() => {
    let isCancelled = false;

    async function loadPage(): Promise<void> {
      try {
        const authenticatedUser = await getCurrentUser();
        if (authenticatedUser === null) {
          router.replace("/login");
          return;
        }

        const response = await fetch(`${API_BASE_URL}/api/users`, {
          credentials: "include",
        });
        if (response.status === 401) {
          router.replace("/login");
          return;
        }
        if (!response.ok) {
          throw new Error("Failed to load users");
        }

        const responseData: unknown = await response.json();
        if (!isUserList(responseData)) {
          throw new Error("Invalid users response");
        }

        if (!isCancelled) {
          setCurrentUser(authenticatedUser);
          setUsers(responseData);
        }
      } catch {
        if (!isCancelled) {
          setErrorMessage("ユーザー一覧を取得できませんでした。");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadPage();
    return () => {
      isCancelled = true;
    };
  }, [router]);

  async function handleSelectUser(targetUser: User): Promise<void> {
    setOpeningUserId(targetUser.id);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/rooms/dm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ target_user_id: targetUser.id }),
      });

      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      if (!response.ok) {
        throw new Error("Failed to open a DM room");
      }

      const responseData: unknown = await response.json();
      if (!isRoom(responseData)) {
        throw new Error("Invalid room response");
      }

      router.push(`/chat/${responseData.id}`);
    } catch {
      setErrorMessage("チャットルームを開けませんでした。");
    } finally {
      setOpeningUserId(null);
    }
  }

  async function handleLogout(): Promise<void> {
    try {
      await logoutCurrentUser();
    } finally {
      router.replace("/login");
    }
  }

  if (isLoading) {
    return (
      <main className="page-shell">
        <section className="content-card loading-card" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true" />
          <p>ユーザーを読み込んでいます...</p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="content-card home-card">
        <header className="home-header">
          <div>
            <p className="eyebrow">2WINS Chat</p>
            <h1>メッセージ</h1>
            {currentUser && (
              <p className="signed-in-user">
                <span className="status-dot" aria-hidden="true" />
                {currentUser.username} としてログイン中
              </p>
            )}
          </div>

          <div className="header-actions">
            {currentUser?.is_admin && (
              <Link className="secondary-button" href="/admin">
                管理
              </Link>
            )}
            <button
              className="secondary-button"
              type="button"
              onClick={() => void handleLogout()}
            >
              ログアウト
            </button>
          </div>
        </header>

        {errorMessage && (
          <p className="alert alert-error" role="alert">{errorMessage}</p>
        )}

        <UserList
          users={users}
          onSelectUser={handleSelectUser}
          openingUserId={openingUserId}
        />
      </section>
    </main>
  );
}
