import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMatches, Match } from '../lib/api'
import { Search, Filter } from 'lucide-react'

function MatchRow({ item }: { item: Match }) {
  return (
    <li className="rounded-3xl border border-border bg-surface3 p-4 shadow-card transition hover:-translate-y-0.5 hover:bg-surface2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <Link to={`/matches/${item.id}`} className="text-lg font-semibold text-white hover:text-accent">
            {item.venue}
          </Link>
          <p className="mt-1 text-sm text-muted">{new Date(item.kickoff_datetime).toLocaleString()}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-background px-3 py-1 text-muted">{(item as any).status ?? 'Scheduled'}</span>
          <span className="rounded-full bg-background px-3 py-1 text-muted">{item.id}</span>
        </div>
      </div>
    </li>
  )
}

export function MatchesPage() {
  const { data: matches = [], isLoading, error } = useQuery({ queryKey: ['matches'], queryFn: getMatches })
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [competitionFilter, setCompetitionFilter] = useState('')
  const [seasonFilter, setSeasonFilter] = useState('')

  const competitionOptions = useMemo(() => Array.from(new Set(matches.map((match) => match.competition_id || ''))).filter(Boolean), [matches])
  const seasonOptions = useMemo(() => Array.from(new Set(matches.map((match) => match.season_id || ''))).filter(Boolean), [matches])

  const filteredMatches = useMemo(() => {
    return matches.filter((match) => {
      const query = search.toLowerCase()
      const status = (match as any).status?.toLowerCase() ?? 'scheduled'
      const competition = (match.competition_id || '').toLowerCase()
      const season = (match.season_id || '').toLowerCase()

      if (search && !match.venue.toLowerCase().includes(query) && !match.id.toLowerCase().includes(query) && !competition.includes(query) && !season.includes(query)) {
        return false
      }
      if (statusFilter && status !== statusFilter) {
        return false
      }
      if (competitionFilter && competition !== competitionFilter) {
        return false
      }
      if (seasonFilter && season !== seasonFilter) {
        return false
      }
      return true
    })
  }, [matches, search, statusFilter, competitionFilter, seasonFilter])

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-8 shadow-card">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Matches</h1>
            <p className="mt-3 text-muted">Search, filter and manage your match library.</p>
          </div>
          <div>
            <Link to="/matches/new" className="btn-primary">
              Create Match
            </Link>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="relative block">
            <Search size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search matches, venue, competition or season"
              className="input pl-11"
            />
          </label>
          <label className="block">
            <span className="label">Status filter</span>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input">
              <option value="">All statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="live">Live</option>
              <option value="finished">Finished</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>
          <label className="block">
            <span className="label">Competition</span>
            <select value={competitionFilter} onChange={(e) => setCompetitionFilter(e.target.value)} className="input">
              <option value="">All competitions</option>
              {competitionOptions.map((competition) => (
                <option key={competition} value={competition}>{competition}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="label">Season</span>
            <select value={seasonFilter} onChange={(e) => setSeasonFilter(e.target.value)} className="input">
              <option value="">All seasons</option>
              {seasonOptions.map((season) => (
                <option key={season} value={season}>{season}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
          <span>{filteredMatches.length} match{filteredMatches.length === 1 ? '' : 'es'} displayed</span>
          <span>{matches.length} total</span>
        </div>

        <div className="mt-8">
          {isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-24 rounded-3xl bg-surface3 p-4 skeleton" />
              ))}
            </div>
          )}
          {error && <div className="text-red-400">Failed to load matches</div>}
          {!isLoading && filteredMatches.length === 0 && (
            <div className="rounded-3xl border border-border bg-surface3 p-10 text-center text-muted">
              <p className="text-lg font-semibold text-white">No matches found</p>
              <p className="mt-2">Create a match or import match data to populate the library.</p>
            </div>
          )}
          {!isLoading && filteredMatches.length > 0 && (
            <ul className="grid gap-4">
              {filteredMatches.map((m) => (
                <MatchRow key={m.id} item={m} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
