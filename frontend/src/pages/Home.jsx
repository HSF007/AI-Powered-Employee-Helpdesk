import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="home">
      <h1>What do you need to do?</h1>

      <div className="doors">
        <section className="door door-employee">
          <h2>I need IT help</h2>
          <p>
            Report a problem with your laptop, software, network or access, and follow it until it is fixed.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" to="/employee/new">Raise a ticket</Link>
            <Link className="btn" to="/employee/tickets">My tickets</Link>
          </div>
        </section>

        <section className="door door-support">
          <h2>I work on the support team</h2>
          <p>
            Review incoming tickets, confirm category and priority, add notes and resolve issues.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" to="/support">Open dashboard</Link>
            <Link className="btn" to="/support/queue">Work queue</Link>
          </div>
        </section>
      </div>
    </div>
  );
}