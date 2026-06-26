import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMatch, Match } from '../lib/api'

function Tabs({ matchId }: { matchId: string }) {
  const tabs = ['Overview', 'Import', 'Timeline', 'Analysis', 'Report']
  return (
    <div className="mt-4 border-b border-border">
      <nav className="flex gap-6">
        {tabs.map((t) => (
          <Link key={t} to={`#${t.toLowerCase()}`} className="py-3 text-sm text-muted">
            {t}
          </Link>
        ))}
      </nav>
    </div>
  )
}

export function MatchWorkspacePage() {
  const { matchId } = useParams<{ matchId: string }>()
  const { data: match, isLoading } = useQuery(['match', matchId], () => matchId ? getMatch(matchId) : Promise.resolve(null as any))

  if (!matchId) return <div className="text-muted">Missing match id</div>

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">Match Workspace</h1>
            <p className="mt-1 text-muted">Match: {matchId}</p>
          </div>
        </div>

        <Tabs matchId={matchId} />

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading match…</div>}
          {!isLoading && match && (
            <div className="rounded border border-border p-4 bg-surface3">
              <div className="text-white">{match.venue} — {new Date(match.kickoff_datetime).toLocaleString()}</div>
              <div className="text-muted text-sm">Competition: {match.competition_id} • Season: {match.season_id}</div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
