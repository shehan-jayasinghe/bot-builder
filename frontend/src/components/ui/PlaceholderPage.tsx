type PlaceholderPageProps = {
  title: string;
  description?: string;
};

export function PlaceholderPage({ title, description = "Coming soon." }: PlaceholderPageProps) {
  return (
    <div className="placeholder-page">
      <h1 className="placeholder-page__title">{title}</h1>
      <p className="placeholder-page__description">{description}</p>
    </div>
  );
}
