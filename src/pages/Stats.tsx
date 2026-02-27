import { Link } from "react-router-dom";

function Stats() {
  const statItems = [
    { label: "total courses", value: "2284" },
    { label: "total reviews", value: "126" },
    { label: "average rating", value: "4.2 / 5" },
  ];

  return (
    <main className="page">
      <section className="panel">
        <h2>stats</h2>
        <p>quick numbers students can scan before choosing classes.</p>

        <div className="card-grid">
          {statItems.map((item) => (
            <article key={item.label} className="mini-card stat-card">
              <h3>{item.label}</h3>
              <p className="stat-value">{item.value}</p>
            </article>
          ))}
        </div>

        <Link to="/">go back home</Link>
      </section>
    </main>
  );
}

export default Stats;
