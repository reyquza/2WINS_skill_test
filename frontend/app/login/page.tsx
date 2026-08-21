import LoginForm from "@/components/LoginForm";


export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="eyebrow">Simple direct messaging</p>
        <h1 id="login-title">2WINS Chat</h1>
        <p className="auth-description">
          登録したメールアドレスとパスワードでログインしてください。
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
