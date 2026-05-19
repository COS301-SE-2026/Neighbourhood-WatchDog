"use client";

import { InputHTMLAttributes } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export function Input({ error, className = "", ...props }: Props) {
  return (
    <input
      className={`
        w-full px-3 py-2 text-sm
        bg-[var(--color-ink)]
        border rounded-md
        text-[var(--color-white)]
        placeholder:text-gray-500
        focus:outline-none focus:ring-2 focus:ring-[var(--color-alert-blue)]
        ${error ? "border-[var(--color-threat-red)]" : "border-[var(--color-mist)]"}
        ${className}
      `}
      {...props}
    />
  );
}