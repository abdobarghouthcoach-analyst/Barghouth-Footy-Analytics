import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, Settings, Layers, Home, Shield, CalendarDays, Trophy, ChevronRight, Moon } from 'lucide-react'

const navLinks = [
  { label: 'Home', href: '/', icon: Home },
  { label: 'Matches', href: '/matches', icon: Shield },
  { label: 'Competitions', href: '/competitions', icon: Trophy },
  { label: 'Seasons', href: '/seasons', icon: CalendarDays },
  { label: 'Settings', href: '/settings', icon: Settings },
]

function NavLink({ label, href, active, icon: Icon }: { label: string; href: string; active: boolean; icon: React.ComponentType<any> }) {
  return (
    <Link
      to={href}
      className={
        'flex items-center gap-3 rounded-3xl px-4 py-3 text-sm font-semibold transition-all duration-200 ' +
        (active
          ? 'bg-surface text-white shadow-card ring-1 ring-accent'
          : 'text-muted hover:bg-surface2 hover:text-white hover:shadow-card')
      }
    >
      <Icon size={18} />
      <span>{label}</span>
      {active && <ChevronRight size={16} className="ml-auto text-accent" />}
    </Link>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const activePath = useMemo(() => location.pathname, [location.pathname])

  const routeMapping = useMemo(() => {
    if (activePath === '/') {
      return { title: 'Home', breadcrumb: ['Home'] }
    }
    if (activePath === '/matches') {
      return { title: 'Matches', breadcrumb: ['Home', 'Matches'] }
    }
    if (activePath === '/matches/new') {
      return { title: 'Create Match', breadcrumb: ['Home', 'Matches', 'Create Match'] }
    }
    if (activePath.startsWith('/matches/')) {
      return { title: 'Match workspace', breadcrumb: ['Home', 'Matches', 'Workspace'] }
    }
    if (activePath === '/competitions') {
      return { title: 'Competitions', breadcrumb: ['Home', 'Competitions'] }
    }
    if (activePath === '/seasons') {
      return { title: 'Seasons', breadcrumb: ['Home', 'Seasons'] }
    }
    if (activePath === '/settings') {
      return { title: 'Settings', breadcrumb: ['Home', 'Settings'] }
    }
    return { title: 'Workspace', breadcrumb: ['Home', 'Workspace'] }
  }, [activePath])

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

          <nav className="flex-1 space-y-2 px-2 py-4">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                label={link.label}
                href={link.href}
                active={activePath === link.href}
                icon={link.icon}
              />
            ))}
          </nav>

          <div className="space-y-3 border-t border-border p-4">
            {!collapsed ? (
              <div className="rounded-3xl bg-surface2 p-4 shadow-card">
                <p className="text-xs uppercase tracking-[0.3em] text-muted">Analyst status</p>
                <p className="mt-3 text-sm font-semibold text-white">Ready to analyse today's workflow.</p>
                <p className="mt-2 text-sm text-muted">Review imports and prepare your coach report.</p>
              </div>
            ) : (
              <div className="rounded-3xl bg-surface2 p-3 text-center text-xs text-muted">Analytics</div>
            )}
          </div>
        </aside>

        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex flex-col justify-between border-b border-border bg-surface px-6 py-4 md:flex-row md:items-center">
            <div className="space-y-2">
              <nav className="flex flex-wrap items-center gap-2 text-sm text-muted">
                {routeMapping.breadcrumb.map((crumb, index) => (
                  <span key={crumb} className={index === routeMapping.breadcrumb.length - 1 ? 'text-white' : 'text-muted'}>
                    {crumb}
                    {index < routeMapping.breadcrumb.length - 1 && <span>›</span>}
                  </span>
                ))}
              </nav>
              <div className="flex flex-col gap-1">
                <p className="text-sm uppercase tracking-[0.3em] text-muted">{routeMapping.title}</p>
                <h1 className="text-2xl font-semibold text-white">{routeMapping.title}</h1>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-3 md:mt-0">
              <button aria-label="Toggle theme" className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-surface2 text-muted hover:text-white">
                <Moon size={18} />
              </button>
              <button aria-label="Profile and settings" className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-surface2 text-muted hover:text-white">
                <Settings size={18} />
              </button>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
      </div>
    </div>
  )
}
