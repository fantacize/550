import { Link, useLocation } from "react-router-dom";

function NotFound() {
  const location = useLocation();

  return (
    <main className="page">
      <section className="panel">
        <h2>404</h2>
        <p>page not found: {location.pathname}</p>
        <Link to="/">go back home</Link>
      </section>
    </main>
  );
}

export default NotFound;
