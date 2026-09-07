export default function SignInPage() {
  return (
    <main>
      <h1>Sign in</h1>
      <form>
        <label>
          Email
          <input name="email" type="email" required />
        </label>
        <label>
          Password
          <input name="password" type="password" required />
        </label>
        <button type="submit">Sign in</button>
      </form>
    </main>
  );
}
