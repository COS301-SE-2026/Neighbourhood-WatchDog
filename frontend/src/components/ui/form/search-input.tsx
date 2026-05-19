"use client";

import { Input } from "./input";

interface Props {
  value?: string;
  onChange?: (v: string) => void;
  onClear?: () => void;
}

export function SearchInput({ value, onChange, onClear }: Props) {
  return (
    <div className="relative w-full">
      <span className="absolute left-3 top-2 text-gray-500">⌕</span>

      <Input
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder="Search..."
        className="pl-8 pr-8"
      />

      {value && onClear && (
        <button
          onClick={onClear}
          className="absolute right-3 top-2 text-gray-500"
        >
          ✕
        </button>
      )}
    </div>
  );
}