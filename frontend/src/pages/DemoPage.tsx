export function DemoPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 font-sans text-lg leading-relaxed text-forest-800">
      <h1 className="font-serif text-4xl font-semibold text-forest-900">
        Demo script (5 min)
      </h1>
      <ol className="list-decimal space-y-4 pl-6 text-forest-700/95">
        <li>
          <strong className="font-semibold text-forest-900">Overview</strong> — show C
          layer badge and explain Progressive Trust Envelope.
        </li>
        <li>
          <strong className="font-semibold text-forest-900">Mediation</strong> — run a
          course PDF move intent; show{" "}
          <code className="rounded bg-wash-mist/90 px-1 font-mono text-base text-sage-800">
            policy_digest
          </code>{" "}
          and capability scopes.
        </li>
        <li>
          <strong className="font-semibold text-forest-900">Hooks</strong> — file read
          inside{" "}
          <code className="rounded bg-wash-mist/90 px-1 font-mono text-base text-forest-900">
            sandbox_workspace/
          </code>{" "}
          (dry_run false), then show rollback entry.
        </li>
        <li>
          <strong className="font-semibold text-forest-900">Finance preset</strong> —
          switch to payment URL in Mediation; show prompt/deny and non-inherited trust.
        </li>
        <li>
          <strong className="font-semibold text-forest-900">Heatmap + timeline</strong>{" "}
          — narrate density of risk buckets and authority envelope over time.
        </li>
        <li>
          <strong className="font-semibold text-forest-900">Profile</strong> — bump risk
          aversion, trigger forgetting pass, explain decay.
        </li>
      </ol>
      <p className="text-sm text-stone-600">
        Judges: emphasize OS course tie-in — POSIX path mediation in C, sandboxed exec,
        audit + rollback, capability tokens as an OS-style abstraction.
      </p>
    </div>
  );
}
