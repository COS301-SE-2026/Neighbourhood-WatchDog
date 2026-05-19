"use client";

import { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "secondary",
  children,
  className = "",
  ...props
}: {
  variant?: Variant;
  children: ReactNode;
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  const base = "px-4 py-2 rounded-md text-sm font-medium transition";

  const styles = {
    primary: "bg-blue-600 text-white",
    secondary: "border border-gray-600 text-white",
    ghost: "text-gray-300",
    danger: "bg-red-600 text-white",
  };

  return (
    <button
      className={`${base} ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}