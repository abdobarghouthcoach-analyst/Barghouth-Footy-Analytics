import { useParams, Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMatch, getTeams, Match, Team } from '../lib/api'

function StatusBadge({ status }: { status?: string }) {
  const mapping: Record<string, string> = {
    scheduled: 'bg-slate-600 text-white',
    live: 'bg-green-500 text-black',
    finished: 'bg-violet-600 text-white',
    cancelled: 'bg-red-600 text-white',
    postponed: 'bg-yellow-500 text-black',
  }

  const cls = mapping[status ?? 'scheduled'] ?? 'bg-slate-600 text-white'
  return <span className={`px-3 py-1 rounded-full text-sm font-medium ${cls}`}>{status ?? 'scheduled'}</span>
}

function TabContent({ tab, match }: { tab: string; match: Match | null }) {
  const title = `${tab} — Placeholder`
  const description = {
    Overview: 'High-level match metadata and quick insights will appear here.',
    Import: 'Upload or import event data (CSV, event feed) and mapping tools.',
    Timeline: 'Event timeline and play-by-play visualisations will live here.',
    Analysis: 'Tactical and statistical analysis tools and charts will be available here.',
    Report: 'Generate and manage coach-ready reports and exports from here.',
  }[tab]

  return (
    <div className="rounded border border-border p-6 bg-surface3">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="text-muted mt-2">{description}</p>
      {tab === 'Overview' && match && (
        <div className="mt-4 text-sm text-muted">Created at: {match.created_at ?? '—'}</div>
      )}
    </div>
  )
}

export function MatchWorkspacePage() {
  const { matchId } = useParams<{ matchId: string }>()
  const [active, setActive] = useState('Overview')
  const { data: match, isLoading } = useQuery<Match | null>(['match', matchId], () => (matchId ? getMatch(matchId) : Promise.resolve(null)))
  const { data: teams = [] } = useQuery<Team[]>(['teams'], getTeams)

  const teamMap = useMemo(() => {
    const map = new Map<string, Team>()
    teams.forEach((t) => map.set(t.id, t))
    return map
  }, [teams])

  if (!matchId) return <div className="text-muted">Missing match id</div>

  const home = match ? teamMap.get(match.home_team_id) : undefined
  const away = match ? teamMap.get(match.away_team_id) : undefined

  const tabs = ['Overview', 'Import', 'Timeline', 'Analysis', 'Report']

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div className="flex items-start justify-between gap-6">
          <div>
            <Link to="/matches" className="text-sm text-muted hover:text-white">← Back to Matches</Link>
            <div className="mt-3 flex items-center gap-4">
              <div>
                <div className="text-2xl font-bold text-white">
                  {home ? home.short_name || home.name : 'Home'} <span className="text-muted">vs</span> {away ? away.short_name || away.name : 'Away'}
                </div>
                <div className="text-sm text-muted mt-1">
                  {match ? `${new Date(match.kickoff_datetime).toLocaleString()} • ${match.venue}` : '—'}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <StatusBadge status={match?.status} />
          </div>
        </div>

        {match?.analyst_notes && (
          <div className="mt-4 rounded border border-border p-3 bg-surface3 text-sm text-muted">
            <strong className="text-white">Analyst notes:</strong>
            <div className="mt-2">{match.analyst_notes}</div>
          </div>
        )}

        <div className="mt-4 border-b border-border">
          <nav className="flex gap-6">
            {tabs.map((t) => (
              <button key={t} onClick={() => setActive(t)} className={`py-3 text-sm ${active === t ? 'text-white border-b-2 border-accent' : 'text-muted'}`}>
                {t}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading match…</div>}
          {!isLoading && <TabContent tab={active} match={match} />}
        </div>
      </div>
    </section>
  )
}
