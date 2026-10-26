"use client";

interface DateRangePickerProps {
  readonly startDate: string;
  readonly endDate: string;
  readonly onStartDateChange: (value: string) => void;
  readonly onEndDateChange: (value: string) => void;
}

export function DateRangePicker({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: DateRangePickerProps) {
  const hasBothDates =
    startDate.length > 0 && endDate.length > 0;

  const hasInvalidRange =
    hasBothDates && startDate > endDate;

  const isValidRange =
    hasBothDates && !hasInvalidRange;

  const inputClassName =
    "watchdog-date-input h-9 w-full min-w-0 rounded-md border " +
    "border-border bg-brand-abyss px-2 text-xs text-brand-frost " +
    "outline-none transition-colors [color-scheme:dark] " +
    "hover:border-brand-gunmetal/70 " +
    "focus-visible:border-brand-green/70 " +
    "focus-visible:ring-2 focus-visible:ring-brand-green/20";

  return (
    <section
      aria-label="Incident date range"
      className="rounded-lg border border-border bg-brand-depth px-3 py-3 shadow-sm"
    >
      <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-sm font-semibold text-brand-frost">
          Incident date range
        </h2>

        <p className="text-xs text-brand-ash">
          Applies to the incident heatmap and contours.
        </p>
      </div>

      <fieldset>
        <legend className="sr-only">
          Select incident date range
        </legend>

        <div className="grid gap-2 sm:grid-cols-2">
          <label className="flex items-center gap-2">
            <span className="w-10 shrink-0 text-xs text-brand-ash">
              Start
            </span>

            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) =>
                onStartDateChange(event.target.value)
              }
              aria-label="Start date"
              aria-invalid={hasInvalidRange}
              className={`${inputClassName} ${
                hasInvalidRange
                  ? "border-brand-threat/70 focus-visible:border-brand-threat focus-visible:ring-brand-threat/20"
                  : ""
              }`}
            />
          </label>

          <label className="flex items-center gap-2">
            <span className="w-10 shrink-0 text-xs text-brand-ash">
              End
            </span>

            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(event) =>
                onEndDateChange(event.target.value)
              }
              aria-label="End date"
              aria-invalid={hasInvalidRange}
              className={`${inputClassName} ${
                hasInvalidRange
                  ? "border-brand-threat/70 focus-visible:border-brand-threat focus-visible:ring-brand-threat/20"
                  : ""
              }`}
            />
          </label>
        </div>
      </fieldset>

      {hasInvalidRange && (
        <p
          role="alert"
          aria-live="polite"
          className="mt-2 text-xs text-brand-threat"
        >
          The start date must be before or equal to the end date.
        </p>
      )}

      {isValidRange && (
        <p
          role="status"
          aria-live="polite"
          className="mt-2 text-xs text-brand-green/80"
        >
          Historical incident range is ready.
        </p>
      )}
    </section>
  );
}