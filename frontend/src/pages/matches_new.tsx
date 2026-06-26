import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getCompetitions, getSeasons, getTeams, createMatch, CreateMatchPayload, Competition, Season, Team } from '../lib/api'

export function CreateMatchPage() {
  const navigate = useNavigate()
  const { data: competitions = [] } = useQuery<Competition[]>({ queryKey: ['competitions'], queryFn: getCompetitions })
  const { data: seasons = [] } = useQuery<Season[]>({ queryKey: ['seasons'], queryFn: getSeasons })
  const { data: teams = [] } = useQuery<Team[]>({ queryKey: ['teams'], queryFn: getTeams })

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

  const mutation = useMutation({
    mutationFn: (payload: any) => createMatch(payload),
    onSuccess(data) {
      navigate(`/matches/${data.id}`)
    },
  })

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((s) => ({ ...s, [key]: value }))
  }

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const payload: CreateMatchPayload = {
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
      <div className="rounded-3xl border border-border bg-surface2 p-8 shadow-card max-w-4xl mx-auto">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Create Match</h1>
            <p className="mt-2 text-muted">Set up the next fixture and capture all match-level details.</p>
          </div>
          <div className="rounded-3xl bg-surface3 px-4 py-2 text-sm text-muted">Use the match workspace to import, analyse and report.</div>
        </div>

        <form onSubmit={submit} className="mt-8 space-y-6">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-4">
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
                <label className="label">Kickoff</label>
                <input required type="datetime-local" value={form.kickoff_datetime} onChange={(e) => update('kickoff_datetime', e.target.value)} className="input" />
              </div>
            </div>

            <div className="space-y-4">
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
                <label className="label">Venue</label>
                <input required type="text" value={form.venue} onChange={(e) => update('venue', e.target.value)} className="input" />
              </div>
            </div>
          </div>

          <div>
            <label className="label">Analyst Notes</label>
            <textarea value={form.analyst_notes} onChange={(e) => update('analyst_notes', e.target.value)} className="input h-32" />
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button type="submit" className="btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Creating…' : 'Create Match'}
            </button>
            <p className="text-sm text-muted">Please complete the match details to start the match workspace.</p>
          </div>
        </form>
      </div>
    </section>
  )
}
