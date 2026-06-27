import type { PropsWithChildren } from "react";

export function StatusPanel({ children, title }: PropsWithChildren<{ title: string }>) {
  return (
    <section className="status-panel" aria-label={title}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function EmptyState({ children, title }: PropsWithChildren<{ title: string }>) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}

export function ErrorMessage({ children }: PropsWithChildren) {
  return (
    <p className="form-error" role="alert">
      {children}
    </p>
  );
}

export function LoadingMessage({ children }: PropsWithChildren) {
  return <p role="status">{children}</p>;
}
