import { Link } from 'react-router-dom'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMatches, Match } from '../lib/api'
import { ChevronRight, Plus, FolderOpen, Sparkles, BarChart3 } from 'lucide-react'

const quickActions = [
  { label: 'Create Match', href: '/matches/new', icon: Plus },
  { label: 'Import Match Data', href: '/matches', icon: FolderOpen },
  { label: 'Open Reports', href: '/matches', icon: BarChart3 },
]

function statItem(title: string, value: string) {
  return (
    <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
      <p className="text-sm text-muted">{title}</p>
      <p className="mt-4 text-3xl font-semibold text-white">{value}</p>
    </div>
  )
}

export function DashboardPage() {
  const { data: matches = [], isLoading } = useQuery<Match[]>({ queryKey: ['matches'], queryFn: getMatches })

  const recentMatches = useMemo(
    () =>
      matches
        .slice()
        .sort((a, b) => new Date(b.kickoff_datetime).getTime() - new Date(a.kickoff_datetime).getTime())
        .slice(0, 5),
    [matches],
  )

  const mostRecent = recentMatches[0]

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-accent2">Continue Working</p>
              <h2 className="mt-2 text-3xl font-semibold text-white">Latest match progress</h2>
            </div>
            <div className="rounded-full bg-surface3 px-4 py-2 text-sm text-muted">Live</div>
          </div>

          <div className="mt-6 space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                <div className="h-14 rounded-2xl skeleton" />
                <div className="h-14 rounded-2xl skeleton" />
              </div>
            ) : mostRecent ? (
              <div className="rounded-3xl bg-surface3 p-5">
                <p className="text-sm text-muted">Most recent match</p>
                <h3 className="mt-2 text-2xl font-semibold text-white">
                  {mostRecent.venue} • {new Date(mostRecent.kickoff_datetime).toLocaleDateString()}
                </h3>
                <p className="mt-3 text-sm text-muted">{mostRecent.analyst_notes || 'No analyst notes yet.'}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <span className="rounded-full bg-surface px-3 py-2 text-sm text-muted">{mostRecent.status ?? 'Scheduled'}</span>
                  <Link to={`/matches/${mostRecent.id}`} className="btn-primary inline-flex items-center gap-2">
                    Continue review <ChevronRight size={16} />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="rounded-3xl bg-surface3 p-6 text-center">
                <p className="text-sm uppercase tracking-[0.3em] text-accent2">No recent match</p>
                <h3 className="mt-3 text-2xl font-semibold text-white">Ready to start your first analysis</h3>
                <p className="mt-2 text-sm text-muted">Create a match or import existing data to begin.</p>
                <div className="mt-5 flex justify-center">
                  <Link to="/matches/new" className="btn-primary">
                    Create Match
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-accent2">Quick Actions</p>
                <h3 className="mt-2 text-2xl font-semibold text-white">Move faster</h3>
              </div>
            </div>
            <div className="mt-6 grid gap-3">
              {quickActions.map((action) => (
                <Link
                  key={action.label}
                  to={action.href}
                  className="flex items-center justify-between rounded-3xl border border-border bg-surface3 px-4 py-4 text-sm text-white transition hover:border-accent hover:bg-surface2"
                >
                  <div className="flex items-center gap-3">
                    <action.icon size={18} className="text-accent" />
                    <span>{action.label}</span>
                  </div>
                  <ChevronRight size={18} className="text-muted" />
                </Link>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
            <p className="text-sm uppercase tracking-[0.3em] text-accent2">Product Roadmap</p>
            <h3 className="mt-3 text-2xl font-semibold text-white">Upcoming features</h3>
            <p className="mt-4 text-sm text-muted">Player reports, xG analysis, opposition scouting and export workflows are coming soon.</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {statItem('Matches analysed', `${matches.length}`)}
        {statItem('Active competitions', `${new Set(matches.map((match) => match.competition_id)).size}`)}
        {statItem('Seasons tracked', `${new Set(matches.map((match) => match.season_id)).size}`)}
      </div>

      <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-accent2">Recent Matches</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Latest five fixtures</h3>
          </div>
          <Link to="/matches" className="text-accent hover:text-accent2 text-sm font-semibold">
            View all matches
          </Link>
        </div>

        <div className="mt-6 space-y-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-20 rounded-3xl bg-surface3 p-4 skeleton" />
            ))
          ) : recentMatches.length > 0 ? (
            recentMatches.map((match) => (
              <div key={match.id} className="rounded-3xl border border-border bg-surface3 p-4">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-white">{match.venue}</p>
                    <p className="text-sm text-muted">{new Date(match.kickoff_datetime).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-wrap gap-2 text-sm">
                    <span className="rounded-full bg-background px-3 py-1 text-muted">{match.status ?? 'Scheduled'}</span>
                    <Link to={`/matches/${match.id}`} className="text-accent hover:text-accent2">
                      View match
                    </Link>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-3xl bg-surface3 p-8 text-center text-muted">
              <p className="text-lg font-semibold text-white">No recent fixtures yet</p>
              <p className="mt-2">Create a match or import data to populate your latest analytics.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
