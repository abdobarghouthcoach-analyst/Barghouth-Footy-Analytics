import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMatches, Match } from '../lib/api'

function MatchRow({ item }: { item: Match }) {
  return (
    <li className="flex items-center justify-between px-4 py-3 hover:bg-surface3 rounded">
      <div>
        <Link to={`/matches/${item.id}`} className="text-white font-medium">
          {item.venue} — {new Date(item.kickoff_datetime).toLocaleString()}
        </Link>
        <div className="text-muted text-sm">{item.id}</div>
      </div>
      <div className="text-sm text-muted">{(item as any).status ?? 'scheduled'}</div>
    </li>
  )
}

export function MatchesPage() {
  const { data: matches = [], isLoading, error } = useQuery(['matches'], getMatches)

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-8 shadow-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Matches</h1>
            <p className="mt-3 text-muted">Match library and workflows.</p>
          </div>
          <div>
            <Link to="/matches/new" className="btn-primary">
              Create Match
            </Link>
          </div>
        </div>

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading matches…</div>}
          {error && <div className="text-red-400">Failed to load matches</div>}
          {!isLoading && matches.length === 0 && <div className="text-muted">No matches found.</div>}
          {matches.length > 0 && (
            <ul className="mt-4 divide-y divide-surface3 rounded">
              {matches.map((m) => (
                <MatchRow key={m.id} item={m} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
