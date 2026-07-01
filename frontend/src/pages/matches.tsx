import { Link } from 'react-router-dom'
import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  deleteMatch,
  getCompetitions,
  getEvents,
  getMatchImports,
  getMatches,
  getSeasons,
  getTeams,
  updateMatch,
  Competition,
  Match,
  Season,
  Team,
  UpdateMatchPayload,
} from '../lib/api'
import { Search } from 'lucide-react'

type MatchEditForm = {
  competition_id: string
  season_id: string
  kickoff_datetime: string
  home_team_id: string
  away_team_id: string
  venue: string
  analyst_notes: string
}

function MatchRow({
  item,
  competitions,
  seasons,
  teams,
  isEditing,
  editForm,
  editError,
  isSaving,
  isDeleting,
  onStartEdit,
  onCancelEdit,
  onEditChange,
  onSubmitEdit,
  onDelete,
}: {
  item: Match
  competitions: Competition[]
  seasons: Season[]
  teams: Team[]
  isEditing: boolean
  editForm: MatchEditForm | null
  editError: string | null
  isSaving: boolean
  isDeleting: boolean
  onStartEdit: (match: Match) => void
  onCancelEdit: () => void
  onEditChange: <K extends keyof MatchEditForm>(key: K, value: MatchEditForm[K]) => void
  onSubmitEdit: (event: FormEvent<HTMLFormElement>) => void
  onDelete: (match: Match) => void
}) {
  const matchLabel = formatMatchLabel(item)
  const filteredSeasons = editForm?.competition_id ? seasons.filter((season) => season.competition_id === editForm.competition_id) : seasons

  return (
    <li className="rounded-3xl border border-border bg-surface3 p-4 shadow-card transition hover:-translate-y-0.5 hover:bg-surface2">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <Link to={`/matches/${item.id}`} className="text-lg font-semibold text-white hover:text-accent">
            {matchLabel}
          </Link>
          <p className="mt-1 text-sm text-muted">
            {new Date(item.kickoff_datetime).toLocaleString()}
            {item.venue ? ` - ${item.venue}` : ''}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Link to={`/matches/${item.id}`} className="btn-secondary">
            Open
          </Link>
          <button type="button" className="btn-secondary" onClick={() => onStartEdit(item)} disabled={isDeleting}>
            Edit
          </button>
          <button type="button" className="btn-secondary" onClick={() => onDelete(item)} disabled={isDeleting || isSaving}>
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
          <span className="rounded-full bg-background px-3 py-1 text-muted">{item.status ?? 'Scheduled'}</span>
          <span className="rounded-full bg-background px-3 py-1 text-muted">{item.id}</span>
        </div>
      </div>
      {isEditing && editForm && (
        <form onSubmit={onSubmitEdit} className="mt-5 rounded-2xl border border-border bg-surface p-4">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="label">Competition</span>
              <select className="input" value={editForm.competition_id} onChange={(e) => onEditChange('competition_id', e.target.value)} required>
                <option value="">Select competition</option>
                {competitions.map((competition) => (
                  <option key={competition.id} value={competition.id}>
                    {competition.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="label">Season</span>
              <select className="input" value={editForm.season_id} onChange={(e) => onEditChange('season_id', e.target.value)} required>
                <option value="">Select season</option>
                {filteredSeasons.map((season) => (
                  <option key={season.id} value={season.id}>
                    {season.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="label">Match date</span>
              <input className="input" type="datetime-local" value={editForm.kickoff_datetime} onChange={(e) => onEditChange('kickoff_datetime', e.target.value)} required />
            </label>
            <label className="block">
              <span className="label">Venue</span>
              <input className="input" value={editForm.venue} onChange={(e) => onEditChange('venue', e.target.value)} required />
            </label>
            <label className="block">
              <span className="label">Home Team</span>
              <select className="input" value={editForm.home_team_id} onChange={(e) => onEditChange('home_team_id', e.target.value)} required>
                <option value="">Select home team</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="label">Away Team</span>
              <select className="input" value={editForm.away_team_id} onChange={(e) => onEditChange('away_team_id', e.target.value)} required>
                <option value="">Select away team</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="mt-4 block">
            <span className="label">Notes</span>
            <textarea className="input h-24" value={editForm.analyst_notes} onChange={(e) => onEditChange('analyst_notes', e.target.value)} />
          </label>
          {editError && <p className="mt-3 text-sm text-red-200">{editError}</p>}
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="submit" className="btn-primary" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button type="button" className="btn-secondary" onClick={onCancelEdit} disabled={isSaving}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </li>
  )
}

export function MatchesPage() {
  const queryClient = useQueryClient()
  const { data: matches = [], isLoading, error } = useQuery({ queryKey: ['matches'], queryFn: getMatches })
  const { data: competitions = [] } = useQuery({ queryKey: ['competitions'], queryFn: getCompetitions })
  const { data: seasons = [] } = useQuery({ queryKey: ['seasons'], queryFn: getSeasons })
  const { data: teams = [] } = useQuery({ queryKey: ['teams'], queryFn: getTeams })
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [competitionFilter, setCompetitionFilter] = useState('')
  const [seasonFilter, setSeasonFilter] = useState('')
  const [editingMatchId, setEditingMatchId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<MatchEditForm | null>(null)
  const [editError, setEditError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const updateMutation = useMutation({
    mutationFn: ({ matchId, payload }: { matchId: string; payload: UpdateMatchPayload }) => updateMatch(matchId, payload),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      setEditingMatchId(null)
      setEditForm(null)
      setEditError(null)
    },
    onError(error) {
      setEditError(apiErrorMessage(error))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (matchId: string) => deleteMatch(matchId),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      setActionError(null)
    },
    onError(error) {
      setActionError(apiErrorMessage(error))
    },
  })

  const competitionOptions = useMemo(() => Array.from(new Set(matches.map((match) => match.competition_id || ''))).filter(Boolean), [matches])
  const seasonOptions = useMemo(() => Array.from(new Set(matches.map((match) => match.season_id || ''))).filter(Boolean), [matches])

  const filteredMatches = useMemo(() => {
    return matches.filter((match) => {
      const query = search.toLowerCase()
      const status = match.status?.toLowerCase() ?? 'scheduled'
      const competition = (match.competition_id || '').toLowerCase()
      const season = (match.season_id || '').toLowerCase()
      const matchLabel = formatMatchLabel(match).toLowerCase()
      const venue = (match.venue || '').toLowerCase()

      if (search && !matchLabel.includes(query) && !venue.includes(query) && !match.id.toLowerCase().includes(query) && !competition.includes(query) && !season.includes(query)) {
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

  function startEdit(match: Match) {
    setEditingMatchId(match.id)
    setEditForm({
      competition_id: match.competition_id,
      season_id: match.season_id,
      kickoff_datetime: toDateTimeLocal(match.kickoff_datetime),
      home_team_id: match.home_team_id,
      away_team_id: match.away_team_id,
      venue: match.venue,
      analyst_notes: match.analyst_notes ?? '',
    })
    setEditError(null)
    setActionError(null)
  }

  function updateEditForm<K extends keyof MatchEditForm>(key: K, value: MatchEditForm[K]) {
    setEditForm((current) => {
      if (!current) return current
      const next = { ...current, [key]: value }
      if (key === 'competition_id') next.season_id = ''
      return next
    })
    setEditError(null)
  }

  async function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingMatchId || !editForm) return
    const original = matches.find((match) => match.id === editingMatchId)
    if (!original) return
    if (editForm.home_team_id === editForm.away_team_id) {
      setEditError('Home Team and Away Team must be different.')
      return
    }

    const teamsChanged = original.home_team_id !== editForm.home_team_id || original.away_team_id !== editForm.away_team_id
    if (teamsChanged) {
      let eventsCount = 0
      let importsCount = 0
      try {
        const usage = await getMatchUsageCounts(editingMatchId)
        eventsCount = usage.eventsCount
        importsCount = usage.importsCount
      } catch (error) {
        setEditError(apiErrorMessage(error))
        return
      }
      if (eventsCount > 0 || importsCount > 0) {
        const confirmed = window.confirm('This match already contains imported or manual events.\nChanging teams may make existing events inconsistent.')
        if (!confirmed) return
      }
    }

    updateMutation.mutate({
      matchId: editingMatchId,
      payload: {
        competition_id: editForm.competition_id,
        season_id: editForm.season_id,
        kickoff_datetime: new Date(editForm.kickoff_datetime).toISOString(),
        home_team_id: editForm.home_team_id,
        away_team_id: editForm.away_team_id,
        venue: editForm.venue,
        analyst_notes: editForm.analyst_notes || null,
      },
    })
  }

  async function confirmDelete(match: Match) {
    setActionError(null)
    let eventsCount = 0
    let importsCount = 0
    try {
      const usage = await getMatchUsageCounts(match.id)
      eventsCount = usage.eventsCount
      importsCount = usage.importsCount
    } catch (error) {
      setActionError(apiErrorMessage(error))
      return
    }
    const message =
      eventsCount === 0 && importsCount === 0
        ? 'Delete Match?\n\nThis cannot be undone.'
        : 'Delete Match?\n\nThis will permanently remove:\n\n• Match\n• Manual Events\n• Imported Events\n• Import History\n• Stored Import Files\n\nThis action cannot be undone.'
    if (window.confirm(message)) deleteMutation.mutate(match.id)
  }

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
          {actionError && <div className="mb-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{actionError}</div>}
          {!isLoading && filteredMatches.length === 0 && (
            <div className="rounded-3xl border border-border bg-surface3 p-10 text-center text-muted">
              <p className="text-lg font-semibold text-white">No matches found</p>
              <p className="mt-2">Create a match or import match data to populate the library.</p>
            </div>
          )}
          {!isLoading && filteredMatches.length > 0 && (
            <ul className="grid gap-4">
              {filteredMatches.map((m) => (
                <MatchRow
                  key={m.id}
                  item={m}
                  competitions={competitions}
                  seasons={seasons}
                  teams={teams}
                  isEditing={editingMatchId === m.id}
                  editForm={editingMatchId === m.id ? editForm : null}
                  editError={editingMatchId === m.id ? editError : null}
                  isSaving={updateMutation.isPending}
                  isDeleting={deleteMutation.isPending}
                  onStartEdit={startEdit}
                  onCancelEdit={() => {
                    setEditingMatchId(null)
                    setEditForm(null)
                    setEditError(null)
                  }}
                  onEditChange={updateEditForm}
                  onSubmitEdit={submitEdit}
                  onDelete={confirmDelete}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}

function formatMatchLabel(match: Match) {
  const homeTeam = match.home_team_name || match.home_team_id
  const awayTeam = match.away_team_name || match.away_team_id
  return `${homeTeam} vs ${awayTeam}`
}

function toDateTimeLocal(value: string) {
  const date = new Date(value)
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

function apiErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong.'
}

async function getMatchUsageCounts(matchId: string) {
  const [events, imports] = await Promise.all([getEvents(matchId), getMatchImports(matchId)])
  return { eventsCount: events.length, importsCount: imports.length }
}
