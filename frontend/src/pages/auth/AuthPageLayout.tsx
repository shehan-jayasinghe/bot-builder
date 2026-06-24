import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type AuthPageLayoutProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  footerText?: string;
  footerLinkText?: string;
  footerLinkTo?: string;
};

export function AuthPageLayout({
  title,
  subtitle,
  children,
  footerText,
  footerLinkText,
  footerLinkTo,
}: AuthPageLayoutProps) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__header">
          <p className="auth-card__eyebrow">BOT BUILDER</p>
          <h1 className="auth-card__title">{title}</h1>
          <p className="auth-card__subtitle">{subtitle}</p>
        </div>

        {children}

        {footerLinkTo && footerLinkText && (
          <p className="auth-card__footer">
            {footerText}{" "}
            <Link to={footerLinkTo} className="auth-card__link">
              {footerLinkText}
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
