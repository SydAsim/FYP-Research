"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

const groups = [
  {
    label: "WORKSPACE",
    links: [
      ["/dashboard", "▦", "Overview"],
      ["/calendar", "▣", "Calendar"],
      ["/appointments", "▤", "Appointments"],
      ["/residents", "◫", "Residents"],
      ["/notes", "▧", "Notes"],
      ["/calls", "◉", "Call history"],
      ["/handoffs", "◇", "Human handoffs"],
    ],
  },
  {
    label: "RESEARCH",
    links: [
      ["/evaluation", "▥", "Evaluation"],
      ["/experiments/new", "✧", "New experiment"],
      ["/settings", "⚙", "Settings"],
    ],
  },
] as const;

function lookupId(id: string): string {
  if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(id))
    return `/calls?query=${encodeURIComponent(id)}`;
  return `/calls/${id}/trace`;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const isLanding = pathname === "/";

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const id = search.trim();
    if (id) router.push(lookupId(id));
  }

  if (isLanding) return <>{children}</>;
  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link
          className="brand"
          href="/dashboard"
          onClick={() => setMenuOpen(false)}
        >
          <span className="brand-mark">✦</span>
          <span>
            indigo<span className="brand-accent"> intelligence</span>
            <small>COMMIT AWARE VOICE</small>
          </span>
        </Link>
        <div className="environment-badge">
          <span className="pulse-dot" /> DEMO ENVIRONMENT
        </div>
        <nav aria-label="Main navigation">
          {groups.map((group) => (
            <div className="nav-group" key={group.label}>
              <div className="nav-heading">{group.label}</div>
              {group.links.map(([href, icon, label]) => (
                <Link
                  key={href}
                  className={`nav-link ${pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`)) ? "active" : ""}`}
                  href={href}
                  onClick={() => setMenuOpen(false)}
                >
                  <span className="nav-icon" aria-hidden="true">
                    {icon}
                  </span>
                  {label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="pulse-dot" /> PostgreSQL is the durable authority
        </div>
      </aside>
      {menuOpen && (
        <button
          aria-label="Close navigation"
          className="mobile-scrim"
          onClick={() => setMenuOpen(false)}
        />
      )}
      <div className="main-frame">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMenuOpen(true)}
          >
            ☰
          </button>
          <div className="topbar-title">
            Commit-Aware Voice Agent <span className="topbar-divider">/</span>{" "}
            <span className="topbar-section">Research workspace</span>
          </div>
          <form className="global-search" onSubmit={submitSearch} role="search">
            <label className="sr-only" htmlFor="global-search">
              Search by exact identifier
            </label>
            <span aria-hidden="true">⌕</span>
            <input
              id="global-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search exact trace ID…"
            />
            <kbd>↵</kbd>
          </form>
          <button
            className="icon-button notification-button"
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            onClick={() => setNotificationsOpen(!notificationsOpen)}
          >
            ♧
          </button>
          <span className="actor-badge" title="Synthetic demo operator">
            SD
          </span>
          {notificationsOpen && (
            <div className="notification-panel" role="status">
              Operational notices are shown on their source screens. No new
              notices.
            </div>
          )}
        </header>
        <div className="scope-banner">
          SYNTHETIC RESEARCH DEMO{" "}
          <span>
            Consequential outcomes are confirmed only after verification.
          </span>
        </div>
        <main className="page-content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
