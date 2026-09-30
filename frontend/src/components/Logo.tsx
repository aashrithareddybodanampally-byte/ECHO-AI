/** ECHO-AI mark: sound-wave bars fading into a dot (the "echo"). */
export function Logo({ withText = true, className = "" }: { withText?: boolean; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <defs>
          <linearGradient id="echo-logo-gradient" gradientUnits="userSpaceOnUse" x1="6" y1="6" x2="26" y2="26">
            <stop offset="0" stopColor="#818cf8" />
            <stop offset="1" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="9" fill="#161a2b" />
        <g stroke="url(#echo-logo-gradient)" strokeWidth="2.6" strokeLinecap="round">
          <path d="M8 13v6" />
          <path d="M12.7 9v14" />
          <path d="M17.3 11.5v9" />
          <path d="M22 14.5v3" />
        </g>
        <circle cx="25" cy="16" r="1.4" fill="#22d3ee" />
      </svg>
      {withText && <span className="text-lg font-semibold tracking-tight text-white">ECHO-AI</span>}
    </span>
  );
}
