import { useParams, Link } from 'react-router-dom'
import { FormEvent, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
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
    Events: 'Event timeline and play-by-play visualisations will live here.',
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
  const { data: match, isLoading } = useQuery<Match | null>({
    queryKey: ['match', matchId],
    queryFn: () => (matchId ? getMatch(matchId) : Promise.resolve(null)),
  })
  const { data: teams = [] } = useQuery<Team[]>({ queryKey: ['teams'], queryFn: getTeams })

  const teamMap = useMemo(() => {
    const map = new Map<string, Team>()
    teams.forEach((t) => map.set(t.id, t))
    return map
  }, [teams])

  if (!matchId) return <div className="text-muted">Missing match id</div>

  const home = match ? teamMap.get(match.home_team_id) : undefined
  const away = match ? teamMap.get(match.away_team_id) : undefined

  const tabs = ['Overview', 'Import', 'Events', 'Analysis', 'Report']

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="space-y-4">
            <Link to="/matches" className="text-sm text-accent hover:text-accent2">← Back to Matches</Link>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Match workspace</p>
              <h1 className="mt-2 text-3xl font-semibold text-white">
                {home ? home.short_name || home.name : 'Home'} <span className="text-muted">vs</span> {away ? away.short_name || away.name : 'Away'}
              </h1>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <div className="rounded-3xl border border-border bg-surface3 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-muted">Competition</p>
                <p className="mt-2 text-sm text-white">{match?.competition_id || '—'}</p>
              </div>
              <div className="rounded-3xl border border-border bg-surface3 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-muted">Season</p>
                <p className="mt-2 text-sm text-white">{match?.season_id || '—'}</p>
              </div>
              <div className="rounded-3xl border border-border bg-surface3 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-muted">Venue</p>
                <p className="mt-2 text-sm text-white">{match?.venue || '—'}</p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-surface3 p-5 shadow-card">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Match status</p>
            <div className="mt-3 flex items-center gap-3">
              <StatusBadge status={match?.status} />
              <div className="text-sm text-muted">Kickoff: {match ? new Date(match.kickoff_datetime).toLocaleString() : '—'}</div>
            </div>
            <div className="mt-4 text-sm text-muted">Analyst notes provide context for this report and future exports.</div>
          </div>
        </div>

        <div className="mt-6 border-b border-border">
          <nav className="grid grid-cols-5 gap-2">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setActive(t)}
                className={`rounded-3xl px-4 py-3 text-sm font-semibold transition ${
                  active === t ? 'bg-accent text-black shadow-card' : 'text-muted hover:bg-surface3 hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading match…</div>}
          {!isLoading && active !== 'Events' && active !== 'Import' && <TabContent tab={active} match={match ?? null} />}
          {!isLoading && active === 'Import' && <ImportTab />}
          {!isLoading && active === 'Events' && match && <TimelineTab matchId={match.id} teams={teams} />}
        </div>
      </div>
    </section>
  )
}

function ImportTab() {
  const [provider, setProvider] = useState('veo')
  const [file, setFile] = useState<File | null>(null)

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <h3 className="text-lg font-semibold text-white">Import Match Data</h3>
        <p className="text-muted mt-2">Import match events from video platforms or analyst files. Imported data will appear in the Events feed.</p>

        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <label className={`flex flex-col gap-3 rounded-3xl border p-4 transition ${provider === 'veo' ? 'border-accent bg-surface' : 'border-border bg-surface3'} cursor-pointer`}>
            <input type="radio" name="provider" value="veo" checked={provider === 'veo'} onChange={() => setProvider('veo')} className="hidden" />
            <span className="text-sm font-semibold text-white">Veo Highlights ZIP</span>
            <span className="text-sm text-muted">Upload a Veo match package for event extraction.</span>
          </label>
          <label className={`flex flex-col gap-3 rounded-3xl border p-4 transition ${provider === 'csv' ? 'border-accent bg-surface' : 'border-border bg-surface3'} cursor-pointer`}>
            <input type="radio" name="provider" value="csv" checked={provider === 'csv'} onChange={() => setProvider('csv')} className="hidden" />
            <span className="text-sm font-semibold text-white">Manual CSV</span>
            <span className="text-sm text-muted">Upload event timelines from custom CSV sources.</span>
          </label>
          <div className="rounded-3xl border border-border bg-surface3 p-4 text-muted">
            <p className="text-sm font-semibold text-white">Other / Coming Soon</p>
            <p className="mt-2 text-sm">Additional import providers and automations are planned.</p>
          </div>
        </div>

        <div className="mt-4">
          <input type="file" accept={provider === 'veo' ? '.zip' : '.csv'} onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="" />
          {file && <div className="text-sm text-muted mt-2">Selected: {file.name}</div>}
          <div className="mt-3 text-sm text-muted">No upload yet — local only. Backend upload coming later.</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded border border-border p-6 bg-surface3 text-muted">
          <h4 className="text-white font-medium">Full Match Video</h4>
          <p className="mt-2">Disabled — future feature</p>
        </div>
        <div className="rounded border border-border p-6 bg-surface3 text-muted">
          <h4 className="text-white font-medium">Tactical Pattern Video</h4>
          <p className="mt-2">Disabled — future feature</p>
        </div>
      </div>
    </div>
  )
}

function TimelineTab({ matchId, teams }: { matchId: string; teams: Team[] }) {
  const queryClient = useQueryClient()
  const { data: events = [], isLoading } = useQuery<Event[]>({
    queryKey: ['events', matchId],
    queryFn: () => getEvents(matchId),
    enabled: !!matchId,
  })
  const [showForm, setShowForm] = useState(false)

  const mutation = useMutation({
    mutationFn: (payload: CreateEventPayload) => createEvent(payload),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['events', matchId] })
      setShowForm(false)
    },
  })

  const [form, setForm] = useState({ event_type: '', minute: '0', second: '0', period: '1H', team_id: '' })

  function update<K extends keyof typeof form>(k: K, v: string) {
    setForm((s) => ({ ...s, [k]: v }))
  }

  function submit(e: FormEvent<HTMLFormElement>) {
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
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Events</h3>
          <p className="text-sm text-muted">Track event timeline entries and match actions.</p>
        </div>
        <button className="btn-secondary inline-flex items-center gap-2" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : 'Add Event'}
        </button>
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
            <button className="btn-primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Adding…' : 'Add Event'}</button>
          </div>
        </form>
      )}

      {isLoading && <div className="text-muted">Loading events…</div>}

      {!isLoading && events.length === 0 && (
        <div className="rounded-3xl border border-border bg-surface3 p-8 text-center text-muted">
          <p className="text-lg font-semibold text-white">No events imported yet</p>
          <p className="mt-2">Import match data to see timeline events and player actions here.</p>
        </div>
      )}

      {!isLoading && events.length > 0 && (
        <ul className="space-y-2">
          {events
            .slice()
            .sort((a, b) => a.minute - b.minute || a.second - b.second)
            .map((ev) => (
              <li key={ev.id} className="rounded-3xl border border-border p-4 bg-surface3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-white font-medium">
                    <Clock size={18} />
                    <span>{ev.minute}:{String(ev.second).padStart(2, '0')} — {ev.event_type}</span>
                  </div>
                  <div className="text-muted text-sm">Team: {ev.team_id} {ev.player_id ? `• Player: ${ev.player_id}` : ''}</div>
                  {ev.notes && <div className="text-muted text-sm">Notes: {ev.notes}</div>}
                </div>
                <div className="text-sm text-muted">{new Date(ev.created_at ?? '').toLocaleString()}</div>
              </li>
            ))}
        </ul>
      )}
    </div>
  )
}
