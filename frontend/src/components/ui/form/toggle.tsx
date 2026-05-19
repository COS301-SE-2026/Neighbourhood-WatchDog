"use client";

interface Props {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
}

export function Toggle({ checked, onChange, label }: Props) {
  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-sm text-white">{label}</span>}

      <button
        onClick={() => onChange(!checked)}
        className={`
          w-10 h-5 rounded-full transition
          ${checked ? "bg-[var(--color-alert-blue)]" : "bg-gray-600"}
        `}
      >
        <div
          className={`
            h-4 w-4 bg-white rounded-full transition
            ${checked ? "translate-x-5" : "translate-x-1"}
          `}
        />
      </button>
    </div>
  );
}