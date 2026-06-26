import { FormEvent, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import {
  createEvent,
  getEvents,
  getMatch,
  getMatchImports,
  getTeams,
  uploadVeoHighlightsImport,
  CreateEventPayload,
  Event,
  ImportJob,
  Match,
  Team,
} from '../lib/api'

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
  const title = `${tab} - Placeholder`
  const description = {
    Overview: 'High-level match metadata and quick insights will appear here.',
    Analysis: 'Tactical and statistical analysis tools and charts will be available here.',
    Report: 'Generate and manage coach-ready reports and exports from here.',
  }[tab]

  return (
    <div className="rounded border border-border p-6 bg-surface3">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="text-muted mt-2">{description}</p>
      {tab === 'Overview' && match && <div className="mt-4 text-sm text-muted">Created at: {match.created_at ?? '-'}</div>}
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
    teams.forEach((team) => map.set(team.id, team))
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
            <Link to="/matches" className="text-sm text-accent hover:text-accent2">Back to Matches</Link>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Match workspace</p>
              <h1 className="mt-2 text-3xl font-semibold text-white">
                {home ? home.short_name || home.name : 'Home'} <span className="text-muted">vs</span> {away ? away.short_name || away.name : 'Away'}
              </h1>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <InfoTile label="Competition" value={match?.competition_id || '-'} />
              <InfoTile label="Season" value={match?.season_id || '-'} />
              <InfoTile label="Venue" value={match?.venue || '-'} />
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-surface3 p-5 shadow-card">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Match status</p>
            <div className="mt-3 flex items-center gap-3">
              <StatusBadge status={match?.status} />
              <div className="text-sm text-muted">Kickoff: {match ? new Date(match.kickoff_datetime).toLocaleString() : '-'}</div>
            </div>
            <div className="mt-4 text-sm text-muted">Analyst notes provide context for this report and future exports.</div>
          </div>
        </div>

        <div className="mt-6 border-b border-border">
          <nav className="grid grid-cols-5 gap-2">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActive(tab)}
                className={`rounded-3xl px-4 py-3 text-sm font-semibold transition ${
                  active === tab ? 'bg-accent text-black shadow-card' : 'text-muted hover:bg-surface3 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading match...</div>}
          {!isLoading && active !== 'Events' && active !== 'Import' && <TabContent tab={active} match={match ?? null} />}
          {!isLoading && active === 'Import' && <ImportTab matchId={matchId} />}
          {!isLoading && active === 'Events' && match && <TimelineTab matchId={match.id} teams={teams} />}
        </div>
      </div>
    </section>
  )
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-border bg-surface3 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-muted">{label}</p>
      <p className="mt-2 text-sm text-white">{value}</p>
    </div>
  )
}

function ImportTab({ matchId }: { matchId: string }) {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const { data: imports = [], isLoading } = useQuery<ImportJob[]>({
    queryKey: ['matches', matchId, 'imports'],
    queryFn: () => getMatchImports(matchId),
  })
  const latestImport = imports[0]
  const mutation = useMutation({
    mutationFn: (selectedFile: File) => uploadVeoHighlightsImport(matchId, selectedFile),
    onSuccess() {
      setFile(null)
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'imports'] })
    },
  })

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!file || mutation.isPending) return
    mutation.mutate(file)
  }

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Veo Highlights ZIP</h3>
            <p className="text-muted mt-2">Upload a Veo highlights package to create import-tracked match events.</p>
          </div>
          {latestImport && <ImportStatusBadge status={latestImport.status} />}
        </div>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            <span className="label">Veo Highlights ZIP</span>
            <input type="file" accept=".zip,application/zip" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="input" />
          </label>
          {file && <div className="text-sm text-muted">Selected: {file.name}</div>}
          <button className="btn-primary" type="submit" disabled={!file || mutation.isPending}>
            {mutation.isPending ? 'Uploading...' : 'Upload ZIP'}
          </button>
        </form>

        {mutation.error && <div className="mt-4 rounded-3xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">{(mutation.error as Error).message}</div>}

        {latestImport && (
          <div className="mt-6 rounded-3xl border border-border bg-surface p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm text-muted">Latest import</p>
                <p className="mt-1 font-semibold text-white">{latestImport.original_filename || latestImport.filename}</p>
              </div>
              <div className="text-sm text-muted">
                {latestImport.imported_events_count} event{latestImport.imported_events_count === 1 ? '' : 's'} imported
              </div>
            </div>
            {latestImport.summary && (
              <div className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-3">
                <SummaryValue label="Message" value={String(latestImport.summary.message ?? 'No summary message')} />
                <SummaryValue label="Parsed" value={String(latestImport.summary.events_parsed ?? 0)} />
                <SummaryValue label="Warnings" value={String(latestImport.warnings_count ?? 0)} />
              </div>
            )}
            {latestImport.error_message && <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{latestImport.error_message}</div>}
            {Array.isArray(latestImport.summary?.warnings) && latestImport.summary.warnings.length > 0 && (
              <ul className="mt-4 space-y-2 text-sm text-yellow-100">
                {latestImport.summary.warnings.map((warning, index) => (
                  <li key={`${warning}-${index}`} className="rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-3">
                    {String(warning)}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <h4 className="text-white font-medium">Import history</h4>
        {isLoading && <div className="mt-4 text-muted">Loading imports...</div>}
        {!isLoading && imports.length === 0 && <div className="mt-4 text-muted">No imports for this match yet.</div>}
        {!isLoading && imports.length > 0 && (
          <ul className="mt-4 space-y-3">
            {imports.map((item) => (
              <li key={item.id} className="rounded-3xl border border-border bg-surface p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-white">{item.original_filename || item.filename}</p>
                    <p className="text-sm text-muted">{new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <ImportStatusBadge status={item.status} />
                    <span className="rounded-full bg-background px-3 py-1 text-sm text-muted">{item.imported_events_count} events</span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ImportStatusBadge({ status }: { status: ImportJob['status'] }) {
  const className = status === 'completed' ? 'bg-green-500 text-black' : status === 'failed' ? 'bg-red-600 text-white' : 'bg-yellow-500 text-black'
  return <span className={`rounded-full px-3 py-1 text-sm font-semibold ${className}`}>{status}</span>
}

function SummaryValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-surface3 p-3">
      <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
      <p className="mt-2 text-white">{value}</p>
    </div>
  )
}

function TimelineTab({ matchId, teams }: { matchId: string; teams: Team[] }) {
  const queryClient = useQueryClient()
  const { data: events = [], isLoading } = useQuery<Event[]>({
    queryKey: ['matches', matchId, 'events'],
    queryFn: () => getEvents(matchId),
    enabled: !!matchId,
  })
  const [showForm, setShowForm] = useState(false)

  const mutation = useMutation({
    mutationFn: (payload: CreateEventPayload) => createEvent(payload),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
      setShowForm(false)
    },
  })

  const [form, setForm] = useState({ event_type: '', minute: '0', second: '0', period: '1H', team_id: '' })

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!form.team_id || !form.event_type) return
    mutation.mutate({
      match_id: matchId,
      team_id: form.team_id,
      event_type: form.event_type,
      minute: Number(form.minute),
      second: Number(form.second),
      period: form.period,
      notes: undefined,
    })
  }

  return (
    <div>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Events</h3>
          <p className="text-sm text-muted">Track event timeline entries and match actions.</p>
        </div>
        <button className="btn-secondary inline-flex items-center gap-2" onClick={() => setShowForm((current) => !current)}>
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
              {teams.map((team) => (
                <option key={team.id} value={team.id}>{team.name}</option>
              ))}
            </select>
            <div />
          </div>

          <div className="mt-3">
            <textarea className="input h-24" placeholder="Notes (optional)" />
          </div>

          <div className="mt-3">
            <button className="btn-primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Adding...' : 'Add Event'}</button>
          </div>
        </form>
      )}

      {isLoading && <div className="text-muted">Loading events...</div>}

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
            .sort((first, second) => first.minute - second.minute || first.second - second.second)
            .map((event) => (
              <li key={event.id} className="rounded-3xl border border-border p-4 bg-surface3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3 text-white font-medium">
                    <Clock size={18} />
                    <span>{event.minute}:{String(event.second).padStart(2, '0')} - {event.event_type}</span>
                    <EventSourceBadge event={event} />
                  </div>
                  <div className="text-muted text-sm">Team: {event.team_id} {event.player_id ? `- Player: ${event.player_id}` : ''}</div>
                  {event.notes && <div className="text-muted text-sm">Notes: {event.notes}</div>}
                </div>
                <div className="text-sm text-muted">{event.created_at ? new Date(event.created_at).toLocaleString() : ''}</div>
              </li>
            ))}
        </ul>
      )}
    </div>
  )
}

function EventSourceBadge({ event }: { event: Event }) {
  if (event.source === 'import' || event.provider === 'veo') {
    return <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-black">imported veo</span>
  }
  return <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">manual</span>
}
