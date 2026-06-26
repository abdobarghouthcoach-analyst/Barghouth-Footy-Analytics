export function DashboardPage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4 rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-muted">Dashboard</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">Overview</h2>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
          <p className="text-sm text-muted">Matches</p>
          <p className="mt-3 text-3xl font-semibold text-white">0</p>
        </div>
        <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
          <p className="text-sm text-muted">Competitions</p>
          <p className="mt-3 text-3xl font-semibold text-white">0</p>
        </div>
        <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
          <p className="text-sm text-muted">Seasons</p>
          <p className="mt-3 text-3xl font-semibold text-white">0</p>
        </div>
      </div>
    </section>
  )
}
