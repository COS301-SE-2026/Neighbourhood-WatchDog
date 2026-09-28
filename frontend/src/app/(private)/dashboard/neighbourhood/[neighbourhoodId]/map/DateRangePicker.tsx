"use client";

interface DateRangePickerProps {
  readonly startDate: string;
  readonly endDate: string;
  readonly onStartDateChange: (
    value: string,
  ) => void;
  readonly onEndDateChange: (
    value: string,
  ) => void;
}

export function DateRangePicker({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: DateRangePickerProps) {
  const validRange =
    startDate.length > 0 &&
    endDate.length > 0 &&
    startDate <= endDate;

  const hasInvalidRange =
    startDate.length > 0 &&
    endDate.length > 0 &&
    startDate > endDate;

  const inputClassName =
    "h-11 w-full rounded-md border " +
    "border-border bg-brand-abyss px-3 " +
    "text-sm text-brand-frost " +
    "outline-none transition-colors " +
    "[color-scheme:dark] " +
    "hover:border-brand-gunmetal/70 " +
    "focus-visible:border-brand-green/70 " +
    "focus-visible:ring-2 " +
    "focus-visible:ring-brand-green/20";

  return (
    <section
      aria-label="Incident date range"
      className={
        "rounded-xl border border-border " +
        "bg-brand-depth px-5 py-5 " +
        "shadow-sm"
      }
    >
      <div
        className={
          "mb-5 flex flex-col gap-2 " +
          "border-b border-border/70 pb-4"
        }
      >
        <div className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className={
              "flex size-7 items-center " +
              "justify-center rounded-md " +
              "border border-brand-green/30 " +
              "bg-brand-green/10 text-brand-green"
            }
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="size-4"
            >
              <rect
                x="3"
                y="4"
                width="18"
                height="17"
                rx="2"
              />
              <path d="M16 2v4M8 2v4M3 10h18" />
            </svg>
          </span>

          <h2 className="text-sm font-semibold text-brand-frost">
            Incident date range
          </h2>
        </div>

        <p className="max-w-2xl text-xs leading-relaxed text-brand-ash">
          Choose the period used for historical incident
          contours. The selected range does not change live
          alerts or danger-zone scores.
        </p>
      </div>

      <fieldset>
        <legend className="sr-only">
          Select incident date range
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-ash/80">
              Start date
            </span>

            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) =>
                onStartDateChange(
                  event.target.value,
                )
              }
              aria-label="Start date"
              aria-invalid={
                hasInvalidRange
              }
              className={
                `watchdog-date-input ${inputClassName} ${
                  hasInvalidRange
                    ? "border-brand-threat/70 focus-visible:border-brand-threat focus-visible:ring-brand-threat/20"
                    : ""
                }`
              }
            />

            <span className="text-[11px] text-brand-ash/60">
              Earliest incident date
            </span>
          </label>

          <label className="grid gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-ash/80">
              End date
            </span>

            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(event) =>
                onEndDateChange(
                  event.target.value,
                )
              }
              aria-label="End date"
              aria-invalid={
                hasInvalidRange
              }
              className={
                `watchdog-date-input ${inputClassName} ${
                  hasInvalidRange
                    ? "border-brand-threat/70 focus-visible:border-brand-threat focus-visible:ring-brand-threat/20"
                    : ""
                }`
              }
            />

            <span className="text-[11px] text-brand-ash/60">
              Latest incident date
            </span>
          </label>
        </div>
      </fieldset>

      {hasInvalidRange && (
        <p
          role="alert"
          aria-live="polite"
          className={
            "mt-4 rounded-md border " +
            "border-brand-threat/30 " +
            "bg-brand-threat/10 px-3 py-2 " +
            "text-xs text-brand-threat"
          }
        >
          The start date must be before or equal
          to the end date.
        </p>
      )}

      {validRange && (
        <p
          role="status"
          aria-live="polite"
          className={
            "mt-4 flex items-center gap-2 " +
            "text-xs text-brand-green/80"
          }
        >
          <span
            aria-hidden="true"
            className="size-1.5 rounded-full bg-brand-green"
          />
          Historical contour range is ready.
        </p>
      )}
    </section>
  );
}