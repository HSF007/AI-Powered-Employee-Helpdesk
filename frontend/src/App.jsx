import { Link, Navigate, NavLink, Route, Routes } from "react-router-dom";
import SectionLayout from "./components/layout/SectionLayout";
import Home from "./pages/Home";
import MyTickets from "./pages/employee/MyTickets";
import RaiseTicket from "./pages/employee/RaiseTicket";
import TicketDetails from "./pages/employee/TicketDetails";
import Dashboard from "./pages/support/Dashboard";
import TicketProcessing from "./pages/support/TicketProcessing";
import WorkQueue from "./pages/support/WorkQueue";

const EMPLOYEE_LINKS = [
  { to: "/employee/new", label: "Raise a ticket" },
  { to: "/employee/tickets", label: "My tickets" },
];

const SUPPORT_LINKS = [
  { to: "/support", label: "Dashboard", end: true },
  { to: "/support/queue", label: "Work queue" },
];

export default function App() {
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="ticket-id brand-mark">IT</span>
          Helpdesk
        </Link>
        <nav className="menu" aria-label="Main">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/employee">Employee</NavLink>
          <NavLink to="/support">Support</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<main className="container"><Home /></main>} />

        <Route path="/employee" element={<SectionLayout name="Employee" tone="employee" links={EMPLOYEE_LINKS} />}>
          <Route index element={<Navigate to="new" replace />} />
          <Route path="new" element={<RaiseTicket />} />
          <Route path="tickets" element={<MyTickets />} />
          <Route path="tickets/:id" element={<TicketDetails />} />
        </Route>

        <Route path="/support" element={<SectionLayout name="Support" tone="support" links={SUPPORT_LINKS} />}>
          <Route index element={<Dashboard />} />
          <Route path="queue" element={<WorkQueue />} />
          <Route path="tickets/:id" element={<TicketProcessing />} />
        </Route>

        <Route
          path="*"
          element={
            <main className="container">
              <div className="empty">
                This page does not exist. <Link to="/">Go to the helpdesk home</Link>.
              </div>
            </main>
          }
        />
      </Routes>
    </>
  );
}