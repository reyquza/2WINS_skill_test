import LoginForm from "@/components/LoginForm";


export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="eyebrow">Simple direct messaging</p>
        <h1 id="login-title">Relay</h1>
        <p className="auth-description">
          Sign in with the email address and password you registered.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
