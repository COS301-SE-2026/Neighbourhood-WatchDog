"use client";

import { ReactNode } from "react";

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-md">
      {children}
    </div>
  );
}

Card.Header = function Header({ children }: { children: ReactNode }) {
  return <div className="p-4 border-b border-gray-800">{children}</div>;
};

Card.Body = function Body({ children }: { children: ReactNode }) {
  return <div className="p-4">{children}</div>;
};