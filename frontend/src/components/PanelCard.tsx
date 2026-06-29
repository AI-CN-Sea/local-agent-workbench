import type { ReactNode } from "react";

type PanelCardProps = {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  actions?: ReactNode;
  compact?: boolean;
  className?: string;
};

export function PanelCard({ title, eyebrow, children, actions, compact = false, className = "" }: PanelCardProps) {
  return (
    <section className={`panel-card ${compact ? "panel-card-compact" : ""} ${className}`.trim()}>
      <div className="panel-card-header">
        <div>
          {eyebrow && <span className="panel-eyebrow">{eyebrow}</span>}
          <h2>{title}</h2>
        </div>
        {actions && <div className="panel-actions">{actions}</div>}
      </div>
      <div className="panel-card-body">{children}</div>
    </section>
  );
}
