export function HomePage() {
  return (
    <div className="canvas-page">
      <div className="canvas-page__toolbar">
        <span className="canvas-page__title">Welcome</span>
        <div className="canvas-page__tools">
          <button type="button" className="canvas-tool">Input</button>
          <button type="button" className="canvas-tool">Output</button>
          <button type="button" className="canvas-tool canvas-tool--active">Actions</button>
          <button type="button" className="canvas-tool">Dev</button>
          <button type="button" className="canvas-tool">Flow</button>
          <button type="button" className="canvas-tool">Variable</button>
          <button type="button" className="canvas-tool">Save</button>
        </div>
      </div>
      <div className="canvas-page__workspace">
        <div className="canvas-page__hint">Workflow canvas — coming soon</div>
      </div>
    </div>
  );
}
