import { useParams, Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMatch, getTeams, getEvents, createEvent, Match, Team, Event, CreateEventPayload } from '../lib/api'

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
          {!isLoading && active !== 'Timeline' && <TabContent tab={active} match={match} />}

          {/* Timeline tab: fetch + show events */}
          {!isLoading && active === 'Timeline' && match && (
            <TimelineTab matchId={match.id} teams={teams} />
          )}
        </div>
      </div>
    </section>
  )
}

function TimelineTab({ matchId, teams }: { matchId: string; teams: Team[] }) {
  const queryClient = useQueryClient()
  const { data: events = [], isLoading } = useQuery<Event[]>(['events', matchId], () => getEvents(matchId), { enabled: !!matchId })
  const [showForm, setShowForm] = useState(false)

  const mutation = useMutation((payload: CreateEventPayload) => createEvent(payload), {
    onSuccess() {
      queryClient.invalidateQueries(['events', matchId])
      setShowForm(false)
    },
  })

  const [form, setForm] = useState({ event_type: '', minute: '0', second: '0', period: '1H', team_id: '' })

  function update<K extends keyof typeof form>(k: K, v: string) {
    setForm((s) => ({ ...s, [k]: v }))
  }

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.team_id || !form.event_type) return
    const payload: CreateEventPayload = {
      match_id: matchId,
      team_id: form.team_id,
      event_type: form.event_type,
      minute: Number(form.minute),
      second: Number(form.second),
      period: form.period as any,
      notes: undefined,
    }
    mutation.mutate(payload)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Timeline</h3>
        <div>
          <button className="btn-secondary mr-2" onClick={() => setShowForm((s) => !s)}>
            {showForm ? 'Cancel' : 'Add Event'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={submit} className="mb-4 rounded border border-border p-4 bg-surface3">
          <div className="grid grid-cols-3 gap-3">
            <input className="input" placeholder="Event type" value={form.event_type} onChange={(e) => update('event_type', e.target.value)} required />
            <input className="input" type="number" min={0} placeholder="Minute" value={form.minute} onChange={(e) => update('minute', e.target.value)} required />
            <input className="input" type="number" min={0} max={59} placeholder="Second" value={form.second} onChange={(e) => update('second', e.target.value)} required />
            <select className="input" value={form.period} onChange={(e) => update('period', e.target.value)}>
              <option value="1H">1H</option>
              <option value="2H">2H</option>
              <option value="ET">ET</option>
              <option value="P">P</option>
            </select>
            <select className="input" value={form.team_id} onChange={(e) => update('team_id', e.target.value)} required>
              <option value="">Select team</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
            <div />
          </div>

          <div className="mt-3">
            <textarea className="input h-24" placeholder="Notes (optional)" />
          </div>

          <div className="mt-3">
            <button className="btn-primary" type="submit" disabled={mutation.isLoading}>{mutation.isLoading ? 'Adding…' : 'Add Event'}</button>
          </div>
        </form>
      )}

      {isLoading && <div className="text-muted">Loading events…</div>}

      {!isLoading && events.length === 0 && <div className="text-muted">No events imported yet.</div>}

      {!isLoading && events.length > 0 && (
        <ul className="space-y-2">
          {events
            .slice()
            .sort((a, b) => a.minute - b.minute || a.second - b.second)
            .map((ev) => (
              <li key={ev.id} className="rounded border border-border p-3 bg-surface3 flex justify-between items-start">
                <div>
                  <div className="text-white font-medium">{ev.minute}:{String(ev.second).padStart(2, '0')} — {ev.event_type}</div>
                  <div className="text-muted text-sm mt-1">Team: {ev.team_id} {ev.player_id ? `• Player: ${ev.player_id}` : ''}</div>
                  {ev.notes && <div className="text-muted text-sm mt-1">Notes: {ev.notes}</div>}
                </div>
                <div className="text-sm text-muted">{new Date(ev.created_at ?? '').toLocaleString()}</div>
              </li>
            ))}
        </ul>
      )}
    </div>
  )
}
