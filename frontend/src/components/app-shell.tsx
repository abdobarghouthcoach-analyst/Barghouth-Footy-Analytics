import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, Settings, LayoutDashboard, Layers } from 'lucide-react'

const navLinks = [
  { label: 'Dashboard', href: '/' },
  { label: 'Matches', href: '/matches' },
  { label: 'Competitions', href: '/competitions' },
  { label: 'Seasons', href: '/seasons' },
  { label: 'Settings', href: '/settings' },
]

function NavLink({ label, href, active }: { label: string; href: string; active: boolean }) {
  return (
    <Link
      to={href}
      className={
        'flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ' +
        (active ? 'bg-surface text-white shadow-card' : 'text-muted hover:bg-surface2 hover:text-white')
      }
    >
      <span>{label}</span>
    </Link>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const activePath = useMemo(() => location.pathname, [location.pathname])

  return (
    <div className="min-h-screen bg-background text-text">
      <div className="flex h-screen overflow-hidden">
        <aside
          className={
            'flex flex-col border-r border-border bg-surface text-text transition-all duration-300 ' +
            (collapsed ? 'w-20' : 'w-72')
          }
        >
          <div className="flex h-16 items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-accent text-black">
                BF
              </span>
              {!collapsed && <div>
                <p className="text-sm font-semibold text-white">Barghouth Footy</p>
                <p className="text-xs text-muted">Analytics</p>
              </div>}
            </div>
            <button
              aria-label="Toggle sidebar"
              onClick={() => setCollapsed((value) => !value)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border text-muted hover:bg-surface2 hover:text-white"
            >
              <Menu size={18} />
            </button>
          </div>

          <nav className="flex-1 space-y-1 px-2 py-4">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                label={link.label}
                href={link.href}
                active={activePath === link.href}
              />
            ))}
          </nav>

          <div className="space-y-2 border-t border-border p-4">
            {!collapsed ? (
              <div className="rounded-2xl bg-surface2 p-3 text-sm">
                <p className="font-semibold text-white">Ready to analyze</p>
                <p className="text-muted">Build your first match report.</p>
              </div>
            ) : (
              <div className="rounded-2xl bg-surface2 p-3 text-center text-xs text-muted">Ready</div>
            )}
          </div>
        </aside>

        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-4">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Workspace</p>
              <h1 className="text-2xl font-semibold text-white">Football analytics home</h1>
            </div>
            <div className="inline-flex items-center gap-3 rounded-2xl border border-border bg-surface2 px-4 py-3 text-sm text-muted">
              <Layers size={18} />
              <span>Dark theme</span>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
      </div>
    </div>
  )
}
