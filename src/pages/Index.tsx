import { Link } from "react-router-dom";

function Index() {
  const pages = [
    {
      path: "/",
      name: "home",
      description: "list classes and links to other pages",
    },
    {
      path: "/login",
      name: "login",
      description: "basic sign-in form mockup",
    },
    {
      path: "/stats",
      name: "stats",
      description: "simple boxes with rating summaries",
    },
    {
      path: "/course/101",
      name: "sample course",
      description: "single course page with fake reviews",
    },
  ];

  return (
    <main className="page">
      <section className="panel">
        <h2>project summary</h2>
        <p>
          this demo lets students browse classes, read short reviews, and post
          quick ratings.
        </p>
      </section>

      <section className="panel">
        <h2>pages</h2>
        <div className="card-grid">
          {pages.map((page) => (
            <article key={page.path} className="mini-card">
              <h3>{page.name}</h3>
              <p>{page.description}</p>
              <Link to={page.path}>open page</Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default Index;
