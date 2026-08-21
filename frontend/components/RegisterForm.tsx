"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { API_BASE_URL } from "@/lib/config";
import { isAuthenticatedUser } from "@/types/user";


export default function RegisterForm() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim(),
          password,
        }),
      });

      if (response.status === 409) {
        setErrorMessage("そのユーザー名またはメールアドレスは使用済みです。");
        return;
      }

      if (!response.ok) {
        setErrorMessage("入力内容を確認してください。");
        return;
      }

      const responseData: unknown = await response.json();
      if (!isAuthenticatedUser(responseData)) {
        throw new Error("Invalid registration response");
      }

      router.replace("/home");
    } catch {
      setErrorMessage(
        "サーバーに接続できません。しばらくしてから再度お試しください。",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="field-header">
        <label htmlFor="username">ユーザー名</label>
        <span aria-hidden="true">{username.length}/50</span>
      </div>
      <input
        className="text-input"
        id="username"
        name="username"
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        maxLength={50}
        autoComplete="username"
        autoFocus
        disabled={isSubmitting}
        required
      />

      <label className="field-label" htmlFor="email">メールアドレス</label>
      <input
        className="text-input"
        id="email"
        name="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        autoComplete="email"
        disabled={isSubmitting}
        required
      />

      <label className="field-label" htmlFor="password">パスワード</label>
      <input
        className="text-input"
        id="password"
        name="password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        minLength={8}
        maxLength={128}
        autoComplete="new-password"
        aria-describedby="password-help"
        disabled={isSubmitting}
        required
      />
      <p id="password-help" className="field-help">8文字以上で入力してください。</p>

      {errorMessage && (
        <p className="alert alert-error" role="alert">{errorMessage}</p>
      )}

      <button
        className="primary-button login-button"
        type="submit"
        disabled={
          isSubmitting ||
          !username.trim() ||
          !email.trim() ||
          password.length < 8
        }
      >
        {isSubmitting ? "登録中..." : "アカウントを作成"}
      </button>

      <p className="auth-switch">
        すでにアカウントをお持ちの方は
        <Link href="/login">ログイン</Link>
      </p>
    </form>
  );
}
