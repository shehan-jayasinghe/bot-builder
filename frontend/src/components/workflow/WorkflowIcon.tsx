type WorkflowIconProps = {
  name: string;
  className?: string;
};

export function WorkflowIcon({ name, className = "workflow-icon" }: WorkflowIconProps) {
  switch (name) {
    case "input":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="5" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M12 9v6M9 12h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "message":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M5 6.5h14a1.5 1.5 0 0 1 1.5 1.5v6A1.5 1.5 0 0 1 18 15.5H10l-3.5 3v-3H5A1.5 1.5 0 0 1 3.5 12V8A1.5 1.5 0 0 1 5 6.5Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "output":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M6 7.5h8.5a2 2 0 0 1 2 2v1.5l3 2.5-3 2.5V17a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "actions":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M13 3L5 14h6l-1 7 8-11h-6l1-7Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "dev":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M8 9 4 12l4 3M16 9l4 3-4 3M14 7l-4 10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "flow":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="6" cy="12" r="2" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="18" cy="7" r="2" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="18" cy="17" r="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 11.5h4l2-3.5M12 12.5l4 3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "variable":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 7l3 10M14 7l3 10M6 12h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "save":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 4.5h10l3.5 3.5V19a1.5 1.5 0 0 1-1.5 1.5H6A1.5 1.5 0 0 1 4.5 19V6A1.5 1.5 0 0 1 6 4.5Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 4.5V9h7V4.5" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
    case "action-ai-tasks":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="5" y="8" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="9.5" cy="12.5" r="1" fill="currentColor" />
          <circle cx="14.5" cy="12.5" r="1" fill="currentColor" />
          <path d="M9.5 15h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "action-kb-query":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 6.5h12v11H6V6.5Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M9 10h6M9 13h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "action-integration":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M9 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM15 18a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M11.2 10.2l1.6-1.6M11.2 13.8l1.6 1.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "action-htm":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="8" r="3" stroke="currentColor" strokeWidth="1.8" />
          <path d="M6.5 18.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M16.5 9.5 19 7M19 7l-1.5 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
  }
}
