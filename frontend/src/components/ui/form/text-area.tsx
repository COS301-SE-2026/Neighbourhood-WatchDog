"use client";

import { TextareaHTMLAttributes } from "react";

interface Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export function Textarea({ error, className = "", ...props }: Props) {
  return (
    <textarea
      className={`
        w-full px-3 py-2 text-sm rounded-md
        bg-[var(--color-ink)]
        border
        text-[var(--color-white)]
        placeholder:text-gray-500
        focus:outline-none focus:ring-2 focus:ring-[var(--color-alert-blue)]
        resize-y
        ${error ? "border-[var(--color-threat-red)]" : "border-[var(--color-mist)]"}
        ${className}
      `}
      {...props}
    />
  );
}