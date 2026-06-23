export function AppSwitcher() {
  return (
    <button type="button" className="app-switcher">
      <span className="app-switcher__icon" aria-hidden="true">
        ◉
      </span>
      <span className="app-switcher__name">abc bank</span>
      <span className="app-switcher__chevron" aria-hidden="true">
        ▾
      </span>
    </button>
  );
}
