"use client";

interface Props {
  id: string;
  label: string;
  checked?: boolean;
  onChange?: (v: boolean) => void;
}

export function Checkbox({ id, label, checked, onChange }: Props) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange?.(e.target.checked)}
        className="h-4 w-4 accent-[var(--color-alert-blue)]"
      />
      <span className="text-sm text-white">{label}</span>
    </label>
  );
}