import type { ReactNode } from "react";

type WizardLayoutProps = {
  step: number;
  totalSteps: number;
  stepLabel?: string;
  eyebrow?: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  centered?: boolean;
};

export function WizardLayout({
  step,
  totalSteps,
  stepLabel,
  eyebrow,
  title,
  subtitle,
  children,
  footer,
  centered = false,
}: WizardLayoutProps) {
  return (
    <div className={`agent-wizard ${centered ? "agent-wizard--centered" : ""}`}>
      <div className="agent-wizard__inner">
        {step > 0 ? (
          <div className="agent-wizard__progress">
            <div className="agent-wizard__progress-bar">
              {Array.from({ length: totalSteps }, (_, index) => (
                <span
                  key={index}
                  className={`agent-wizard__progress-segment ${
                    index < step ? "agent-wizard__progress-segment--active" : ""
                  }`}
                />
              ))}
            </div>
            <div className="agent-wizard__progress-meta">
              <span>STEP {step} OF {totalSteps}</span>
              {stepLabel ? <span>{stepLabel}</span> : null}
            </div>
          </div>
        ) : null}

        {eyebrow ? <p className="agent-wizard__eyebrow">{eyebrow}</p> : null}
        <h1 className="agent-wizard__title">{title}</h1>
        {subtitle ? <p className="agent-wizard__subtitle">{subtitle}</p> : null}
        <div className="agent-wizard__body">{children}</div>
        {footer ? <div className="agent-wizard__footer">{footer}</div> : null}
      </div>
    </div>
  );
}
