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
          {!isLoading && active === 'Import' && <ImportTab matchId={matchId} onOpenEvents={() => setActive('Events')} />}
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

function ImportTab({ matchId, onOpenEvents }: { matchId: string; onOpenEvents: () => void }) {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const { data: imports = [], isLoading } = useQuery<ImportJob[]>({
    queryKey: ['matches', matchId, 'imports'],
    queryFn: () => getMatchImports(matchId),
  })
  const latestImport = imports[0]
  const activeImport = latestImport
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
            <p className="text-sm uppercase tracking-[0.3em] text-accent2">Veo Highlights ZIP</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Import Veo Highlights</h3>
            <p className="text-muted mt-3 max-w-3xl">
              BFA imports highlight metadata from a Veo ZIP and creates match events linked to this workspace. The provider is fixed to Veo Highlights ZIP for this slice.
            </p>
          </div>
          {activeImport && <ImportStatusBadge status={activeImport.status} />}
        </div>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            <span className="label">Select Veo ZIP</span>
            <input type="file" accept=".zip" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="input" />
          </label>
          <SelectedFileSummary file={file} />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button className="btn-primary" type="submit" disabled={!file || mutation.isPending}>
              {mutation.isPending ? 'Uploading and importing...' : 'Upload ZIP'}
            </button>
            {mutation.isPending && <span className="text-sm text-muted">Import is running. Keep this tab open while BFA stores and reads the ZIP.</span>}
          </div>
        </form>

        {mutation.error && <ImportApiError error={mutation.error as Error} />}
        {activeImport && <ImportSummary job={activeImport} onOpenEvents={onOpenEvents} />}
      </div>

      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h4 className="text-white font-medium">Import history</h4>
            <p className="mt-1 text-sm text-muted">Recent Veo import jobs for this match.</p>
          </div>
        </div>
        {isLoading && <div className="mt-4 text-muted">Loading imports...</div>}
        {!isLoading && imports.length === 0 && <div className="mt-4 text-muted">No imports for this match yet.</div>}
        {!isLoading && imports.length > 0 && (
          <ul className="mt-4 space-y-3">
            {imports.map((item) => (
              <ImportHistoryItem key={item.id} job={item} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ImportStatusBadge({ status }: { status: ImportJob['status'] }) {
  const className = status === 'completed' ? 'bg-green-500 text-black' : status === 'failed' ? 'bg-red-600 text-white' : 'bg-yellow-500 text-black'
  return <span className={`rounded-full px-3 py-1 text-sm font-semibold capitalize ${className}`}>{status}</span>
}

function SummaryValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-surface3 p-3">
      <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
      <p className="mt-2 text-white">{value}</p>
    </div>
  )
}

function SelectedFileSummary({ file }: { file: File | null }) {
  if (!file) {
    return <div className="rounded-2xl border border-border bg-surface p-4 text-sm text-muted">No ZIP selected yet.</div>
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-muted">Selected file</p>
      <div className="mt-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <span className="font-semibold text-white">{file.name}</span>
        <span className="text-sm text-muted">{formatFileSize(file.size)}</span>
      </div>
    </div>
  )
}

function ImportApiError({ error }: { error: Error }) {
  return (
    <div className="mt-4 rounded-3xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
      <p className="font-semibold text-white">Upload could not start.</p>
      <p className="mt-1">BFA did not receive an import job from the API. Technical detail: {error.message}</p>
    </div>
  )
}

function ImportSummary({ job, onOpenEvents }: { job: ImportJob; onOpenEvents: () => void }) {
  const summary = getImportSummary(job)
  const completedWithZero = job.status === 'completed' && summary.eventsCreated === 0
  const warnings = getWarnings(job)

  return (
    <div className={`mt-6 rounded-3xl border p-5 ${job.status === 'failed' ? 'border-red-500/40 bg-red-500/10' : completedWithZero ? 'border-yellow-500/40 bg-yellow-500/10' : 'border-border bg-surface'}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm text-muted">Latest import</p>
          <p className="mt-1 font-semibold text-white">{job.original_filename || job.filename}</p>
          <p className="mt-2 text-sm text-muted">Provider: Veo Highlights ZIP</p>
        </div>
        <ImportStatusBadge status={job.status} />
      </div>

      <div className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-4">
        <SummaryValue label="Status" value={job.status} />
        <SummaryValue label="Events created" value={String(summary.eventsCreated)} />
        {summary.eventsSkipped !== null && <SummaryValue label="Events skipped" value={String(summary.eventsSkipped)} />}
        <SummaryValue label="Warnings" value={String(warnings.length || job.warnings_count || 0)} />
      </div>

      {job.status === 'completed' && summary.eventsCreated > 0 && (
        <div className="mt-4 rounded-2xl border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-100">
          <p className="font-semibold text-white">Import completed.</p>
          <p className="mt-1">Imported events are now available in the Events tab.</p>
          <button type="button" className="btn-secondary mt-3" onClick={onOpenEvents}>
            Open Events tab
          </button>
        </div>
      )}

      {completedWithZero && (
        <div className="mt-4 rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-100">
          Import completed, but 0 events were created. Review warnings and source metadata before continuing.
        </div>
      )}

      {job.status === 'failed' && (
        <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          <p className="font-semibold text-white">Import failed.</p>
          <p className="mt-1">{job.error_message || 'BFA could not import events from this ZIP.'}</p>
        </div>
      )}

      {warnings.length > 0 && (
        <ul className="mt-4 space-y-2 text-sm text-yellow-100">
          {warnings.map((warning, index) => (
            <li key={`${warning}-${index}`} className="rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-3">
              {warning}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ImportHistoryItem({ job }: { job: ImportJob }) {
  const summary = getImportSummary(job)
  const warnings = getWarnings(job)
  return (
    <li className="rounded-3xl border border-border bg-surface p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="font-semibold text-white">{job.original_filename || job.filename}</p>
          <p className="mt-1 text-sm text-muted">Provider: {job.provider === 'veo' ? 'Veo Highlights ZIP' : job.provider}</p>
          <p className="mt-1 text-sm text-muted">Created: {formatDateTime(job.created_at)}</p>
          <p className="mt-1 text-sm text-muted">Completed: {job.completed_at ? formatDateTime(job.completed_at) : '-'}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ImportStatusBadge status={job.status} />
          <span className="rounded-full bg-background px-3 py-1 text-sm text-muted">{summary.eventsCreated} events</span>
          {(warnings.length > 0 || job.error_message) && (
            <span className={`rounded-full px-3 py-1 text-sm ${job.error_message ? 'bg-red-600 text-white' : 'bg-yellow-500 text-black'}`}>
              {job.error_message ? 'Error' : `${warnings.length} warning${warnings.length === 1 ? '' : 's'}`}
            </span>
          )}
        </div>
      </div>
    </li>
  )
}

function getImportSummary(job: ImportJob) {
  const summary = job.summary ?? {}
  return {
    eventsCreated: toNumber(summary.events_created ?? summary.events_imported ?? job.imported_events_count),
    eventsSkipped: summary.events_skipped === undefined ? null : toNumber(summary.events_skipped),
  }
}

function getWarnings(job: ImportJob): string[] {
  const warnings = job.summary?.warnings
  return Array.isArray(warnings) ? warnings.map((warning) => String(warning)) : []
}

function toNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kilobytes = bytes / 1024
  if (kilobytes < 1024) return `${kilobytes.toFixed(1)} KB`
  return `${(kilobytes / 1024).toFixed(1)} MB`
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString()
}

function formatEventName(eventType: string) {
  return eventType
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function formatMatchTime(event: Event) {
  const prefix = event.period ? `${event.period} ` : ''
  return `${prefix}${event.minute}:${String(event.second).padStart(2, '0')}`
}

function getClipIndex(event: Event): number | null {
  const value = event.raw_payload?.clip_index
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function formatClipReference(event: Event) {
  const clipIndex = getClipIndex(event)
  return clipIndex === null ? null : `Clip #${String(clipIndex).padStart(2, '0')}`
}

function getOriginalFilename(event: Event) {
  const value = event.raw_payload?.filename
  return typeof value === 'string' && value.trim() ? value : null
}

function getPeriodSortValue(period?: string | null) {
  const order: Record<string, number> = { '1H': 1, '2H': 2, ET: 3, P: 4 }
  return period ? order[period] ?? 50 : 99
}

function sortEventsForReview(first: Event, second: Event) {
  const periodDelta = getPeriodSortValue(first.period) - getPeriodSortValue(second.period)
  if (periodDelta !== 0) return periodDelta

  const clockDelta = first.minute * 60 + first.second - (second.minute * 60 + second.second)
  if (clockDelta !== 0) return clockDelta

  const firstClip = getClipIndex(first) ?? Number.MAX_SAFE_INTEGER
  const secondClip = getClipIndex(second) ?? Number.MAX_SAFE_INTEGER
  if (firstClip !== secondClip) return firstClip - secondClip

  const firstCreated = first.created_at ? new Date(first.created_at).getTime() : Number.MAX_SAFE_INTEGER
  const secondCreated = second.created_at ? new Date(second.created_at).getTime() : Number.MAX_SAFE_INTEGER
  if (firstCreated !== secondCreated) return firstCreated - secondCreated

  return first.id.localeCompare(second.id)
}

function TimelineTab({ matchId, teams }: { matchId: string; teams: Team[] }) {
  const queryClient = useQueryClient()
  const teamNames = useMemo(() => new Map(teams.map((team) => [team.id, team.name])), [teams])
  const { data: events = [], isLoading } = useQuery<Event[]>({
    queryKey: ['matches', matchId, 'events'],
    queryFn: () => getEvents(matchId),
    enabled: !!matchId,
  })
  const [showForm, setShowForm] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const sortedEvents = useMemo(() => events.slice().sort(sortEventsForReview), [events])
  const selectedEvent = selectedEventId ? sortedEvents.find((event) => event.id === selectedEventId) ?? null : null

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
          <p className="text-lg font-semibold text-white">No events have been recorded yet.</p>
          <p className="mt-2">Import a Veo Highlights ZIP or add events manually.</p>
        </div>
      )}

      {!isLoading && events.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <ul className="space-y-3">
            {sortedEvents.map((event) => {
                const teamLabel = event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team'
                const clipReference = formatClipReference(event)
                const isSelected = selectedEventId === event.id
                return (
                  <li key={event.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedEventId(event.id)}
                      className={`w-full rounded-3xl border p-4 text-left transition hover:border-accent hover:bg-surface ${
                        isSelected ? 'border-accent bg-surface' : 'border-border bg-surface3'
                      }`}
                    >
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-3">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="inline-flex items-center gap-2 rounded-full bg-background px-3 py-1 text-sm font-semibold text-white">
                              <Clock size={16} />
                              {formatMatchTime(event)}
                            </span>
                            <EventSourceBadge event={event} />
                            {clipReference && <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">{clipReference}</span>}
                          </div>
                          <div>
                            <p className="text-lg font-semibold text-white">{formatEventName(event.event_type)}</p>
                            <p className="mt-1 text-sm text-muted">Team: {teamLabel}</p>
                          </div>
                        </div>
                        <div className="text-sm text-muted">{event.created_at ? formatDateTime(event.created_at) : ''}</div>
                      </div>
                    </button>
                  </li>
                )
              })}
          </ul>

          <EventDetailsPanel
            event={selectedEvent}
            resolveTeamLabel={(event) => (event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team')}
          />
        </div>
      )}
    </div>
  )
}

function EventDetailsPanel({ event, resolveTeamLabel }: { event: Event | null; resolveTeamLabel: (event: Event) => string }) {
  if (!event) {
    return (
      <aside className="rounded-3xl border border-border bg-surface3 p-5 text-sm text-muted xl:sticky xl:top-6">
        Select an event to review its details.
      </aside>
    )
  }

  const clipReference = formatClipReference(event)
  const originalFilename = getOriginalFilename(event)

  return (
    <aside className="rounded-3xl border border-border bg-surface3 p-5 xl:sticky xl:top-6">
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-2 rounded-full bg-background px-3 py-1 text-sm font-semibold text-white">
          <Clock size={16} />
          {formatMatchTime(event)}
        </span>
        <EventSourceBadge event={event} />
      </div>

      <h4 className="mt-4 text-xl font-semibold text-white">{formatEventName(event.event_type)}</h4>

      <div className="mt-5 space-y-3 text-sm">
        <DetailRow label="Event type" value={formatEventName(event.event_type)} />
        <DetailRow label="Match time" value={formatMatchTime(event)} />
        <DetailRow label="Team" value={resolveTeamLabel(event)} />
        <DetailRow label="Player" value={event.player_id || 'Unknown player'} />
        <DetailRow label="Provider" value={event.provider === 'veo' ? 'Veo' : event.provider || '-'} />
        <DetailRow label="Source" value={event.source === 'import' ? 'Import' : 'Manual'} />
        <DetailRow label="Clip number" value={clipReference || '-'} />
        <DetailRow label="Original filename" value={originalFilename || '-'} />
        <DetailRow label="Import Job ID" value={event.import_job_id || '-'} />
      </div>

      {event.raw_payload && (
        <details className="mt-5 rounded-2xl border border-border bg-surface p-4">
          <summary className="cursor-pointer text-sm font-semibold text-white">Developer payload</summary>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-muted">
            {JSON.stringify(event.raw_payload, null, 2)}
          </pre>
        </details>
      )}
    </aside>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
      <p className="mt-1 break-words text-white">{value}</p>
    </div>
  )
}

function EventSourceBadge({ event }: { event: Event }) {
  if (event.source === 'import' || event.provider === 'veo') {
    return <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-black">Veo Import</span>
  }
  return <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">Manual</span>
}
