import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getCompetitions, getSeasons, getTeams, createMatch, Competition, Season, Team } from '../lib/api'

export function CreateMatchPage() {
  const navigate = useNavigate()
  const { data: competitions = [] } = useQuery<Competition[]>(['competitions'], getCompetitions)
  const { data: seasons = [] } = useQuery<Season[]>(['seasons'], getSeasons)
  const { data: teams = [] } = useQuery<Team[]>(['teams'], getTeams)

  const [form, setForm] = useState({
    competition_id: '',
    season_id: '',
    home_team_id: '',
    away_team_id: '',
    kickoff_datetime: '',
    venue: '',
    analyst_notes: '',
  })

  const filteredSeasons = useMemo(() => {
    if (!form.competition_id) return seasons
    return seasons.filter((s) => s.competition_id === form.competition_id)
  }, [seasons, form.competition_id])

  const mutation = useMutation((payload: any) => createMatch(payload), {
    onSuccess(data) {
      navigate(`/matches/${data.id}`)
    },
  })

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((s) => ({ ...s, [key]: value }))
  }

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      competition_id: form.competition_id,
      season_id: form.season_id,
      home_team_id: form.home_team_id,
      away_team_id: form.away_team_id,
      kickoff_datetime: new Date(form.kickoff_datetime).toISOString(),
      venue: form.venue,
      analyst_notes: form.analyst_notes || null,
    }
    mutation.mutate(payload)
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-8 shadow-card max-w-3xl">
        <h1 className="text-2xl font-semibold text-white">Create Match</h1>
        <p className="mt-2 text-muted">Create a new match and begin analysis workflows.</p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Competition</label>
              <select required value={form.competition_id} onChange={(e) => update('competition_id', e.target.value)} className="input">
                <option value="">Select competition</option>
                {competitions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Season</label>
              <select required value={form.season_id} onChange={(e) => update('season_id', e.target.value)} className="input">
                <option value="">Select season</option>
                {filteredSeasons.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Home Team</label>
              <select required value={form.home_team_id} onChange={(e) => update('home_team_id', e.target.value)} className="input">
                <option value="">Select home team</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Away Team</label>
              <select required value={form.away_team_id} onChange={(e) => update('away_team_id', e.target.value)} className="input">
                <option value="">Select away team</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Kickoff</label>
              <input required type="datetime-local" value={form.kickoff_datetime} onChange={(e) => update('kickoff_datetime', e.target.value)} className="input" />
            </div>

            <div>
              <label className="label">Venue</label>
              <input required type="text" value={form.venue} onChange={(e) => update('venue', e.target.value)} className="input" />
            </div>
          </div>

          <div>
            <label className="label">Analyst Notes</label>
            <textarea value={form.analyst_notes} onChange={(e) => update('analyst_notes', e.target.value)} className="input h-28" />
          </div>

          <div className="flex items-center gap-3">
            <button type="submit" className="btn-primary" disabled={mutation.isLoading}>
              {mutation.isLoading ? 'Creating…' : 'Create Match'}
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
