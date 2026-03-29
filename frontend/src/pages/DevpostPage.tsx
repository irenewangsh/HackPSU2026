export function DevpostPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 font-sans text-lg leading-relaxed text-forest-800">
      <h1 className="font-serif text-4xl font-semibold text-forest-900">
        Devpost
      </h1>
      <section className="glass-panel-soft space-y-3 p-7">
        <h2 className="font-serif text-2xl font-semibold text-forest-900">
          Inspiration
        </h2>
        <p className="text-forest-700/95">
          OS agents can touch files, browsers, and shells. Permission mistakes are not
          “LLM bugs”; they are{" "}
          <span className="font-medium text-sage-800">operating system problems</span>{" "}
          — least privilege, mediation, and isolation.
        </p>
      </section>
      <section className="glass-panel space-y-4 p-7">
        <h2 className="font-serif text-2xl font-semibold text-forest-900">
          What it does
        </h2>
        <p className="text-forest-700/95">
          SentinelOS is a supervisory control plane: every agent capability is a
          structured intent. A sensitivity + risk engine computes a decision (allow /
          transform / prompt / deny) and a{" "}
          <strong className="text-forest-900">Progressive Trust Envelope</strong>.
        </p>
        <p className="text-forest-700/95">
          <strong className="text-forest-900">Three C translation units</strong>{" "}
          implement the OS-facing surface:{" "}
          <code className="rounded bg-paper-3/90 px-1 font-mono text-sm">sentinel_policy.c</code>{" "}
          (<code className="font-mono text-sage-800">realpath</code>, containment,
          FNV-1a),{" "}
          <code className="rounded bg-paper-3/90 px-1 font-mono text-sm">sentinel_fs.c</code>{" "}
          (<code className="font-mono text-sage-800">lstat</code>), and{" "}
          <code className="rounded bg-paper-3/90 px-1 font-mono text-sm">sentinel_exec.c</code>{" "}
          (<code className="font-mono text-sage-800">fork</code>/
          <code className="font-mono text-sage-800">pipe</code>/
          <code className="font-mono text-sage-800">execve</code>,{" "}
          <code className="font-mono text-sage-800">RLIMIT_CPU</code>). Python
          orchestrates policy; process creation is POSIX code.
        </p>
        <p className="text-forest-700/95">
          <strong className="text-forest-900">HMAC capability tokens</strong> encode
          scopes + policy digest. Hooks run inside{" "}
          <code className="rounded bg-paper-3/90 px-1 font-mono text-sm">
            sandbox_workspace/
          </code>
          .
        </p>
      </section>
      <section className="glass-panel space-y-3 p-7">
        <h2 className="font-serif text-2xl font-semibold text-forest-900">
          How we built it
        </h2>
        <ul className="list-disc space-y-2 pl-6 text-forest-700/95">
          <li>FastAPI control plane + SQLite audit / reversible ops</li>
          <li>C shared library + Python ctypes</li>
          <li>React console with heatmap + authority timeline</li>
        </ul>
      </section>
      <section className="glass-panel-soft space-y-3 p-7">
        <h2 className="font-serif text-2xl font-semibold text-forest-900">
          Course connection
        </h2>
        <p className="text-forest-700/95">
          Maps to OS themes:{" "}
          <strong className="text-forest-900">
            capabilities, access control, sandboxing, auditing, C systems programming
          </strong>
          . The abstraction is a policy mediator where a reference monitor would sit —
          not inside the model.
        </p>
      </section>
    </div>
  );
}
