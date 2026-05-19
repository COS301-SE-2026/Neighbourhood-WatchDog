"use client";

import { JSX, ReactNode } from "react";

export function Heading({
  level = 2,
  children,
  className = "",
}: {
  level?: 1 | 2 | 3 | 4;
  children: ReactNode;
  className?: string;
}) {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;

  const sizeMap = {
    1: "text-3xl font-bold",
    2: "text-2xl font-semibold",
    3: "text-xl font-semibold",
    4: "text-sm font-semibold uppercase tracking-widest",
  };

  return (
    <Tag className={`${sizeMap[level]} ${className}`}>
      {children}
    </Tag>
  );
}

export function Text({
  size = "sm",
  muted = false,
  children,
  className = "",
}: {
  size?: "xs" | "sm" | "base" | "lg";
  muted?: boolean;
  children: ReactNode;
  className?: string;
}) {
  const sizeMap = {
    xs: "text-xs",
    sm: "text-sm",
    base: "text-base",
    lg: "text-lg",
  };

  return (
    <p
      className={`${sizeMap[size]} ${
        muted ? "text-gray-400" : "text-white"
      } ${className}`}
    >
      {children}
    </p>
  );
}