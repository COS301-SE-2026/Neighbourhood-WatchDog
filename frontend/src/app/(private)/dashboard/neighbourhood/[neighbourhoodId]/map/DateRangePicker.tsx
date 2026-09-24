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

  return (
    <section
      aria-label="Incident date range"
      className="rounded-lg border border-border bg-brand-depth px-4 py-4"
    >
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-brand-frost">
          Incident date range
        </h2>

        <p className="mt-1 text-xs text-brand-ash">
          Choose the period used for historical incident contours.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="text-xs font-medium text-brand-ash">
            Start date
          </span>

          <input
            type="date"
            value={startDate}
            max={endDate || undefined}
            onChange={(event) =>
              onStartDateChange(event.target.value)
            }
            aria-label="Start date"
            className="rounded-md border border-border bg-brand-abyss px-3 py-2 text-sm text-brand-frost outline-none focus:border-brand-green"
          />
        </label>

        <label className="grid gap-1.5">
          <span className="text-xs font-medium text-brand-ash">
            End date
          </span>

          <input
            type="date"
            value={endDate}
            min={startDate || undefined}
            onChange={(event) =>
              onEndDateChange(event.target.value)
            }
            aria-label="End date"
            className="rounded-md border border-border bg-brand-abyss px-3 py-2 text-sm text-brand-frost outline-none focus:border-brand-green"
          />
        </label>
      </div>

      {!validRange &&
        startDate.length > 0 &&
        endDate.length > 0 && (
          <p
            role="alert"
            className="mt-3 text-xs text-brand-threat"
          >
            The start date must be before or equal to the end date.
          </p>
        )}
    </section>
  );
}