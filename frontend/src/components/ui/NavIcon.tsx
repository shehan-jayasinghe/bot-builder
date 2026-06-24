type NavIconProps = {
  name: string;
  className?: string;
};

export function NavIcon({ name, className = "nav-icon" }: NavIconProps) {
  switch (name) {
    case "agent":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="7" width="14" height="12" rx="3" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="9.5" cy="12" r="1.2" fill="currentColor" />
          <circle cx="14.5" cy="12" r="1.2" fill="currentColor" />
          <path d="M9.5 15.5h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M12 7V4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "workflows":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 6h5v5H6V6Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M13 13h5v5h-5v-5Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M11 8.5h2.5l2 2.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "data-sources":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <ellipse cx="12" cy="7" rx="7" ry="3" stroke="currentColor" strokeWidth="1.8" />
          <path d="M5 7v4c0 1.7 3.1 3 7 3s7-1.3 7-3V7" stroke="currentColor" strokeWidth="1.8" />
          <path d="M5 11v4c0 1.7 3.1 3 7 3s7-1.3 7-3v-4" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
    case "channels":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 8.5h3.5L11 5v14l-3.5-3.5H4v-7Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
          <path d="M14 9.5c1.8 1 3 2.7 3 4.5s-1.2 3.5-3 4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "conversations":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M5 6.5h14a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H9l-4 3v-3.5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "analytics":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 17V11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M12 17V7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M18 17v-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "schedulers":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4.5" y="6.5" width="15" height="13" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 4.5v3M16 4.5v3M4.5 10.5h15" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "settings":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M12 4.5v2M12 17.5v2M4.5 12h2M17.5 12h2M6.8 6.8l1.4 1.4M15.8 15.8l1.4 1.4M17.2 6.8l-1.4 1.4M8.2 15.8l-1.4 1.4"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "sub-agents":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="9" cy="9" r="3" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="16.5" cy="10.5" r="2.5" stroke="currentColor" strokeWidth="1.8" />
          <path d="M4.5 18.5c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "skills":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M14.5 5.5l4 4-8.5 8.5H6v-4L14.5 5.5Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
        </svg>
      );
    case "memory":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="6" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 10h8M8 14h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "llm":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="5" width="14" height="14" rx="3" stroke="currentColor" strokeWidth="1.8" />
          <path d="M9 9h6M9 12h6M9 15h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="7" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
  }
}
