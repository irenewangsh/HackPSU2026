import { motion } from "framer-motion";

export function TrustRing({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="relative flex h-44 w-44 items-center justify-center">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r="52"
          fill="none"
          stroke="rgba(63, 90, 74, 0.12)"
          strokeWidth="10"
        />
        <motion.circle
          cx="60"
          cy="60"
          r="52"
          fill="none"
          stroke="url(#grad-ring-editorial)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={326.7}
          initial={{ strokeDashoffset: 326.7 }}
          animate={{ strokeDashoffset: 326.7 * (1 - value) }}
          transition={{ type: "spring", stiffness: 80, damping: 18 }}
        />
        <defs>
          <linearGradient id="grad-ring-editorial" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6b9a82" />
            <stop offset="50%" stopColor="#4a7c62" />
            <stop offset="100%" stopColor="#2f4f40" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="font-serif text-4xl font-semibold text-forest-900">{pct}%</span>
        <span className="font-sans text-[10px] font-medium uppercase tracking-[0.2em] text-forest-600/75">
          Trust envelope
        </span>
      </div>
    </div>
  );
}
