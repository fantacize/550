import { Link } from "react-router-dom";

function Login() {
  return (
    <main className="page">
      <section className="panel form-panel">
        <h2>login</h2>
        <p>basic form mockup for student account access.</p>
        <form className="simple-form">
          <label htmlFor="username">username</label>
          <input id="username" name="username" type="text" placeholder="admin" />

          <label htmlFor="password">password</label>
          <input
            id="password"
            name="password"
            type="password"
            placeholder="password"
          />

          <button type="button">sign in</button>
        </form>
        <Link to="/">go back home</Link>
      </section>
    </main>
  );
}

export default Login;
