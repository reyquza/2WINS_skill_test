import RegisterForm from "@/components/RegisterForm";


export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="register-title">
        <p className="eyebrow">Create your account</p>
        <h1 id="register-title">新規登録</h1>
        <p className="auth-description">
          ユーザー名、メールアドレス、パスワードを登録します。
        </p>
        <RegisterForm />
      </section>
    </main>
  );
}
