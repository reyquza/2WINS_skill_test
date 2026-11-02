"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { API_BASE_URL } from "@/lib/config";
import { isAuthenticatedUser } from "@/types/user";


export default function LoginForm() {
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
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      if (response.status === 401) {
        setErrorMessage("The email address or password is incorrect.");
        return;
      }

      if (!response.ok) {
        setErrorMessage("Please check the information you entered.");
        return;
      }

      const responseData: unknown = await response.json();
      if (!isAuthenticatedUser(responseData)) {
        throw new Error("Invalid login response");
      }

      router.replace("/home");
    } catch {
      setErrorMessage(
        "We could not reach the server. Please try again in a moment.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="email">Email address</label>
      <input
        className="text-input"
        id="email"
        name="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        autoComplete="email"
        autoFocus
        disabled={isSubmitting}
        required
      />

      <label className="field-label" htmlFor="password">Password</label>
      <input
        className="text-input"
        id="password"
        name="password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        minLength={8}
        maxLength={128}
        autoComplete="current-password"
        disabled={isSubmitting}
        required
      />

      {errorMessage && (
        <p className="alert alert-error" role="alert">{errorMessage}</p>
      )}

      <button
        className="primary-button login-button"
        type="submit"
        disabled={isSubmitting || !email.trim() || password.length < 8}
      >
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>

      <p className="auth-switch">
        New to Relay?{" "}
        <Link href="/register">Create an account</Link>
      </p>
    </form>
  );
}
