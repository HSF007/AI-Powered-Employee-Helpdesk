import { NavLink, Outlet } from "react-router-dom";

// Wraps one area (Employee or Support): section bar with its own menu,
// then the active page rendered through <Outlet />.
export default function SectionLayout({ name, tone, links }) {
  return (
    <div className={`section section-${tone}`}>
      <div className="section-bar">
        <div className="section-bar-inner">
          <span className="section-name">{name}</span>
          <nav className="subnav" aria-label={`${name} pages`}>
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
      <main className="container">
        <Outlet />
      </main>
    </div>
  );
}