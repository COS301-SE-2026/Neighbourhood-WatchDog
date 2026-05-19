"use client";

import { SelectHTMLAttributes } from "react";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export function Select({ error, className = "", children, ...props }: Props) {
  return (
    <select
      className={`
        w-full px-3 py-2 text-sm rounded-md
        bg-[var(--color-ink)]
        border
        text-[var(--color-white)]
        focus:outline-none focus:ring-2 focus:ring-[var(--color-alert-blue)]
        ${error ? "border-[var(--color-threat-red)]" : "border-[var(--color-mist)]"}
        ${className}
      `}
      {...props}
    >
      {children}
    </select>
  );
}