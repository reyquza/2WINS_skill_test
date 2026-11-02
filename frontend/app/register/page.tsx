import RegisterForm from "@/components/RegisterForm";


export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="register-title">
        <p className="eyebrow">Create your account</p>
        <h1 id="register-title">Create an account</h1>
        <p className="auth-description">
          Choose a username and register with your email and password.
        </p>
        <RegisterForm />
      </section>
    </main>
  );
}
