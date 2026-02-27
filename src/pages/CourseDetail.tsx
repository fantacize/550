import { Link, useParams } from "react-router-dom";

function CourseDetail() {
  const { courseid } = useParams();
  const reviewSnippets = [
    "good class, fair grading, and clear homework expectations.",
    "workload can be heavy during project weeks but still manageable.",
    "lectures are straightforward and examples help a lot for quizzes.",
  ];

  return (
    <main className="page">
      <section className="panel">
        <h2>course detail</h2>
        <p>
          showing course id: <strong>{courseid}</strong>
        </p>
        <p>sample metrics: overall 4.3, workload 3.4, interest 4.6</p>

        <h3>recent comments</h3>
        <ul className="review-list">
          {reviewSnippets.map((snippet) => (
            <li key={snippet}>{snippet}</li>
          ))}
        </ul>

        <Link to="/">go back home</Link>
      </section>
    </main>
  );
}

export default CourseDetail;
