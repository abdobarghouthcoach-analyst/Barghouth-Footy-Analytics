import { useMemo, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  getCompetitions,
  getSeasons,
  getTeams,
  createCompetition,
  createSeason,
  createTeam,
  createMatch,
  CreateMatchPayload,
  Competition,
  Season,
  Team,
} from '../lib/api'

type SetupForm = {
  competition_id: string
  season_id: string
  home_team_id: string
  away_team_id: string
  kickoff_datetime: string
  venue: string
  analyst_notes: string
}

type TeamTarget = 'home_team_id' | 'away_team_id'

function defaultSeasonDates() {
  const year = new Date().getFullYear()
  return {
    start_date: `${year}-07-01`,
    end_date: `${year + 1}-06-30`,
  }
}

function apiErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong.'
}

function upsertById<T extends { id: string }>(items: T[], item: T) {
  return items.some((existing) => existing.id === item.id) ? items.map((existing) => (existing.id === item.id ? item : existing)) : [...items, item]
}

export function CreateMatchPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: competitions = [] } = useQuery<Competition[]>({ queryKey: ['competitions'], queryFn: getCompetitions })
  const { data: seasons = [] } = useQuery<Season[]>({ queryKey: ['seasons'], queryFn: getSeasons })
  const { data: teams = [] } = useQuery<Team[]>({ queryKey: ['teams'], queryFn: getTeams })

  const [form, setForm] = useState<SetupForm>({
    competition_id: '',
    season_id: '',
    home_team_id: '',
    away_team_id: '',
    kickoff_datetime: '',
    venue: '',
    analyst_notes: '',
  })
  const [competitionName, setCompetitionName] = useState('')
  const [seasonName, setSeasonName] = useState('')
  const [teamForms, setTeamForms] = useState<Record<TeamTarget, { name: string; short_name: string }>>({
    home_team_id: { name: '', short_name: '' },
    away_team_id: { name: '', short_name: '' },
  })
  const [openCreate, setOpenCreate] = useState<Record<'competition' | 'season' | TeamTarget, boolean>>({
    competition: false,
    season: false,
    home_team_id: false,
    away_team_id: false,
  })
  const [formError, setFormError] = useState<string | null>(null)

  const filteredSeasons = useMemo(() => {
    if (!form.competition_id) return seasons
    return seasons.filter((s) => s.competition_id === form.competition_id)
  }, [seasons, form.competition_id])

  const createCompetitionMutation = useMutation({
    mutationFn: createCompetition,
    async onSuccess(data) {
      queryClient.setQueryData<Competition[]>(['competitions'], (items = []) => upsertById(items, data))
      await queryClient.invalidateQueries({ queryKey: ['competitions'] })
      setForm((s) => ({ ...s, competition_id: data.id, season_id: '' }))
      setCompetitionName('')
      setOpenCreate((s) => ({ ...s, competition: false }))
    },
  })

  const createSeasonMutation = useMutation({
    mutationFn: createSeason,
    async onSuccess(data) {
      queryClient.setQueryData<Season[]>(['seasons'], (items = []) => upsertById(items, data))
      await queryClient.invalidateQueries({ queryKey: ['seasons'] })
      setForm((s) => ({ ...s, competition_id: data.competition_id, season_id: data.id }))
      setSeasonName('')
      setOpenCreate((s) => ({ ...s, season: false }))
    },
  })

  const createTeamMutation = useMutation({
    mutationFn: ({ target, name, short_name }: { target: TeamTarget; name: string; short_name?: string | null }) =>
      createTeam({ name, short_name: short_name || null }).then((team) => ({ team, target })),
    async onSuccess({ team, target }) {
      queryClient.setQueryData<Team[]>(['teams'], (items = []) => upsertById(items, team))
      await queryClient.invalidateQueries({ queryKey: ['teams'] })
      setForm((s) => ({ ...s, [target]: team.id }))
      setTeamForms((s) => ({ ...s, [target]: { name: '', short_name: '' } }))
      setOpenCreate((s) => ({ ...s, [target]: false }))
    },
  })

  const createMatchMutation = useMutation({
    mutationFn: (payload: CreateMatchPayload) => createMatch(payload),
    onSuccess(data) {
      navigate(`/matches/${data.id}`)
    },
  })

  const sameTeamsSelected = Boolean(form.home_team_id && form.away_team_id && form.home_team_id === form.away_team_id)
  const canCreateMatch = !createMatchMutation.isPending && !sameTeamsSelected

  function update<K extends keyof SetupForm>(key: K, value: string) {
    setForm((s) => {
      const next = { ...s, [key]: value }
      if (key === 'competition_id') next.season_id = ''
      return next
    })
    setFormError(null)
  }

  function submitCompetition() {
    const name = competitionName.trim()
    if (!name) return
    createCompetitionMutation.mutate({
      name,
      country: 'Not specified',
      level: 'first',
      competition_type: 'league',
    })
  }

  function submitSeason() {
    const name = seasonName.trim()
    if (!name || !form.competition_id) return
    createSeasonMutation.mutate({
      name,
      competition_id: form.competition_id,
      is_active: true,
      ...defaultSeasonDates(),
    })
  }

  function submitTeam(target: TeamTarget) {
    const values = teamForms[target]
    const name = values.name.trim()
    if (!name) return
    createTeamMutation.mutate({ target, name, short_name: values.short_name.trim() || null })
  }

  function submitMatch(e: FormEvent) {
    e.preventDefault()
    if (sameTeamsSelected) {
      setFormError('Home Team and Away Team must be different.')
      return
    }
    const payload: CreateMatchPayload = {
      competition_id: form.competition_id,
      season_id: form.season_id,
      home_team_id: form.home_team_id,
      away_team_id: form.away_team_id,
      kickoff_datetime: new Date(form.kickoff_datetime).toISOString(),
      venue: form.venue,
      analyst_notes: form.analyst_notes || null,
    }
    createMatchMutation.mutate(payload)
  }

  return (
    <section className="space-y-6">
      <div className="mx-auto max-w-4xl rounded-3xl border border-border bg-surface2 p-8 shadow-card">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Create Match</h1>
            <p className="mt-2 text-muted">Set up the next fixture and capture all match-level details.</p>
          </div>
          <div className="rounded-3xl bg-surface3 px-4 py-2 text-sm text-muted">Use the match workspace to import, analyse and report.</div>
        </div>

        <form onSubmit={submitMatch} className="mt-8 space-y-6">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-4">
              <div>
                <label className="label">Competition</label>
                <select required value={form.competition_id} onChange={(e) => update('competition_id', e.target.value)} className="input">
                  <option value="">{competitions.length ? 'Select competition' : 'No competitions yet'}</option>
                  {competitions.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <InlineAction
                  label="Create new competition"
                  open={openCreate.competition}
                  onToggle={() => setOpenCreate((s) => ({ ...s, competition: !s.competition }))}
                />
                {openCreate.competition ? (
                  <InlineCreateForm
                    error={createCompetitionMutation.error ? apiErrorMessage(createCompetitionMutation.error) : null}
                  >
                    <input
                      required
                      type="text"
                      value={competitionName}
                      onChange={(e) => setCompetitionName(e.target.value)}
                      className="input"
                      placeholder="Competition name"
                    />
                    <button type="button" className="btn-primary" disabled={createCompetitionMutation.isPending} onClick={submitCompetition}>
                      {createCompetitionMutation.isPending ? 'Creating...' : 'Create'}
                    </button>
                  </InlineCreateForm>
                ) : null}
              </div>

              <TeamSelector
                label="Home Team"
                value={form.home_team_id}
                teams={teams}
                emptyLabel="No teams yet"
                onChange={(value) => update('home_team_id', value)}
                open={openCreate.home_team_id}
                onToggle={() => setOpenCreate((s) => ({ ...s, home_team_id: !s.home_team_id }))}
                values={teamForms.home_team_id}
                onValuesChange={(values) => setTeamForms((s) => ({ ...s, home_team_id: values }))}
                onSubmit={() => submitTeam('home_team_id')}
                pending={createTeamMutation.isPending}
                error={createTeamMutation.error ? apiErrorMessage(createTeamMutation.error) : null}
              />

              <div>
                <label className="label">Kickoff</label>
                <input required type="datetime-local" value={form.kickoff_datetime} onChange={(e) => update('kickoff_datetime', e.target.value)} className="input" />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Season</label>
                <select required value={form.season_id} onChange={(e) => update('season_id', e.target.value)} className="input">
                  <option value="">{filteredSeasons.length ? 'Select season' : 'No seasons for this competition'}</option>
                  {filteredSeasons.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                <InlineAction
                  label="Create new season"
                  open={openCreate.season}
                  disabled={!form.competition_id}
                  onToggle={() => setOpenCreate((s) => ({ ...s, season: !s.season }))}
                />
                {!form.competition_id ? <p className="mt-2 text-sm text-muted">Create or select a competition before adding a season.</p> : null}
                {openCreate.season && form.competition_id ? (
                  <InlineCreateForm
                    error={createSeasonMutation.error ? apiErrorMessage(createSeasonMutation.error) : null}
                  >
                    <input
                      required
                      type="text"
                      value={seasonName}
                      onChange={(e) => setSeasonName(e.target.value)}
                      className="input"
                      placeholder="Season name"
                    />
                    <button type="button" className="btn-primary" disabled={createSeasonMutation.isPending} onClick={submitSeason}>
                      {createSeasonMutation.isPending ? 'Creating...' : 'Create'}
                    </button>
                  </InlineCreateForm>
                ) : null}
              </div>

              <TeamSelector
                label="Away Team"
                value={form.away_team_id}
                teams={teams}
                emptyLabel="No teams yet"
                onChange={(value) => update('away_team_id', value)}
                open={openCreate.away_team_id}
                onToggle={() => setOpenCreate((s) => ({ ...s, away_team_id: !s.away_team_id }))}
                values={teamForms.away_team_id}
                onValuesChange={(values) => setTeamForms((s) => ({ ...s, away_team_id: values }))}
                onSubmit={() => submitTeam('away_team_id')}
                pending={createTeamMutation.isPending}
                error={createTeamMutation.error ? apiErrorMessage(createTeamMutation.error) : null}
              />

              <div>
                <label className="label">Venue</label>
                <input required type="text" value={form.venue} onChange={(e) => update('venue', e.target.value)} className="input" />
              </div>
            </div>
          </div>

          {sameTeamsSelected ? <p className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">Home Team and Away Team must be different.</p> : null}

          <div>
            <label className="label">Analyst Notes</label>
            <textarea value={form.analyst_notes} onChange={(e) => update('analyst_notes', e.target.value)} className="input h-32" />
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button type="submit" className="btn-primary" disabled={!canCreateMatch}>
              {createMatchMutation.isPending ? 'Creating...' : 'Create Match'}
            </button>
            <p className="text-sm text-muted">Please complete the match details to start the match workspace.</p>
          </div>
          {formError ? <p className="text-sm text-red-200">{formError}</p> : null}
          {createMatchMutation.error ? <p className="text-sm text-red-200">{apiErrorMessage(createMatchMutation.error)}</p> : null}
        </form>
      </div>
    </section>
  )
}

function InlineAction({
  label,
  open,
  disabled,
  onToggle,
}: {
  label: string
  open: boolean
  disabled?: boolean
  onToggle: () => void
}) {
  return (
    <button type="button" className="mt-2 text-sm font-semibold text-accent disabled:cursor-not-allowed disabled:text-muted" disabled={disabled} onClick={onToggle}>
      {open ? 'Cancel' : label}
    </button>
  )
}

function InlineCreateForm({ children, error }: { children: ReactNode; error: string | null }) {
  return (
    <div
      className="mt-3 rounded-2xl border border-border bg-surface3 p-4"
      onKeyDown={(event) => {
        if (event.key === 'Enter') event.preventDefault()
      }}
    >
      <div className="flex flex-col gap-3 sm:flex-row">{children}</div>
      {error ? <p className="mt-2 text-sm text-red-200">{error}</p> : null}
    </div>
  )
}

function TeamSelector({
  label,
  value,
  teams,
  emptyLabel,
  onChange,
  open,
  onToggle,
  values,
  onValuesChange,
  onSubmit,
  pending,
  error,
}: {
  label: string
  value: string
  teams: Team[]
  emptyLabel: string
  onChange: (value: string) => void
  open: boolean
  onToggle: () => void
  values: { name: string; short_name: string }
  onValuesChange: (values: { name: string; short_name: string }) => void
  onSubmit: () => void
  pending: boolean
  error: string | null
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <select required value={value} onChange={(e) => onChange(e.target.value)} className="input">
        <option value="">{teams.length ? `Select ${label.toLowerCase()}` : emptyLabel}</option>
        {teams.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      <InlineAction label="Create new team" open={open} onToggle={onToggle} />
      {open ? (
        <InlineCreateForm error={error}>
          <input
            required
            type="text"
            value={values.name}
            onChange={(e) => onValuesChange({ ...values, name: e.target.value })}
            className="input"
            placeholder="Team name"
          />
          <input
            type="text"
            value={values.short_name}
            onChange={(e) => onValuesChange({ ...values, short_name: e.target.value })}
            className="input"
            placeholder="Short name"
          />
          <button type="button" className="btn-primary" disabled={pending} onClick={onSubmit}>
            {pending ? 'Creating...' : 'Create'}
          </button>
        </InlineCreateForm>
      ) : null}
    </div>
  )
}
