"use client";

import { useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import type { ScriptableContext } from "chart.js";
import { TimeIntervalsEnum, TimePeriod } from "@/lib/validators/alert";
import { useAlertFrequencyMetrics } from "@/hooks/use-alert-metrics";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

interface AlertFrequencyMetricsProps {
  neighbourhoodId: string;
  timeInt?: TimeIntervalsEnum;
  timePer?: TimePeriod;
}

const DEFAULT_CHART_THEME = {
  blue: "#2D7EFF",
  sky: "#6AB0FF",
  navy: "#F5F5F5",
  mist: "#8A8A8A",
  body: "#A3A3A3",
  card: "#141414",
  border: "rgb(138 138 138 / 12%)",
  font: "Inter, system-ui, sans-serif",
};

function readChartTheme() {
  if (typeof window === "undefined") {
    return DEFAULT_CHART_THEME;
  }

  const styles = getComputedStyle(document.documentElement);

  const read = (name: string, fallback: string) =>
    styles.getPropertyValue(name).trim() || fallback;

  return {
    blue: read("--color-pulse", DEFAULT_CHART_THEME.blue),
    sky: read("--color-ice", DEFAULT_CHART_THEME.sky),
    navy: read("--color-frost", DEFAULT_CHART_THEME.navy),
    mist: read("--color-gunmetal", DEFAULT_CHART_THEME.mist),
    body: read("--color-ash", DEFAULT_CHART_THEME.body),
    card: read("--card", DEFAULT_CHART_THEME.card),
    border: read("--border-subtle", DEFAULT_CHART_THEME.border),
    font: read("--font-sans", DEFAULT_CHART_THEME.font),
  };
}

function useChartTheme() {
  const [theme] = useState(readChartTheme);

  return theme;
}

export function AlertFrequencyGraph({
  neighbourhoodId,
  timeInt,
  timePer,
}: AlertFrequencyMetricsProps) {
  const [timeInterval, setTimeInterval] = useState<TimeIntervalsEnum>(
    timeInt ? timeInt : "DAILY",
  );
  const [timePeriod, setTimePeriod] = useState<TimePeriod>(
    timePer ? timePer : "MONTH",
  );

  const { metrics, loading, error } = useAlertFrequencyMetrics(
    neighbourhoodId,
    timeInterval,
    timePeriod,
  );

  const theme = useChartTheme();

  const dates = metrics?.period;
  const counts = metrics?.count;

  const chartData = useMemo(() => {
    if (!dates || !counts) return null;

    return {
      labels: dates.map((d) =>
        new Date(d).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
        }),
      ),
      datasets: [
        {
          label: "Alerts",
          data: counts,
          borderColor: theme.blue,
          backgroundColor: (context: ScriptableContext<"line">) => {
            const chart = context.chart;
            const { ctx, chartArea } = chart;

            if (!chartArea) return theme.sky;

            const gradient = ctx.createLinearGradient(
              0,
              chartArea.top,
              0,
              chartArea.bottom,
            );

            gradient.addColorStop(0, `${theme.blue}33`);
            gradient.addColorStop(1, `${theme.blue}00`);

            return gradient;
          },
          // fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: theme.blue,
          pointBorderColor: theme.navy,
          pointBorderWidth: 1.5,
        },
      ],
    };
  }, [dates, counts, theme]);

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index" as const, intersect: false },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: "Alert Frequency",
          align: "start" as const,
          color: theme.navy,
          font: { family: theme.font, size: 16, weight: "bold" as const },
          padding: { bottom: 16 },
        },
        tooltip: {
          backgroundColor: theme.card,
          titleColor: theme.navy,
          bodyColor: theme.body,
          borderColor: theme.border,
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          displayColors: false,
          titleFont: { family: theme.font, weight: 600 },
          bodyFont: { family: theme.font },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { color: theme.border },
          ticks: {
            color: theme.body,
            font: { family: theme.font, size: 11 },
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: theme.mist },
          border: { display: false },
          ticks: {
            color: theme.body,
            font: { family: theme.font, size: 11 },
            precision: 0,
          },
        },
      },
    }),
    [theme],
  );

  return (
    <div
      className="rounded-lg p-6 w-full bg-card border"
      style={{ borderColor: "var(--border)", boxShadow: "var(--shadow-sm)" }}
    >
      <div className="h-72">
        {loading ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            Loading…
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-sm text-destructive">
            {error}
          </div>
        ) : chartData ? (
          <Line data={chartData} options={options} />
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            No data available
          </div>
        )}
      </div>

      <div className="flex justify-around p-4">
        {" "}
        {/** Filter buttons */}
        <select
          name="selectInterval"
          value={timeInterval}
          onChange={(e) => {
            setTimeInterval(e.target.value as TimeIntervalsEnum);
          }}
        >
          <option value="DAILY">Daily</option>
          <option value="MONTHLY">Monthly</option>
          <option value="YEARLY">Yearly</option>
        </select>

        <select
          name="selectPeriod"
          value={timePeriod}
          onChange={(e) => {
            setTimePeriod(e.target.value as TimePeriod);
          }}
        >
          <option value="WEEK">Week</option>
          <option value="MONTH">Month</option>
          <option value="THREE_MONTHS">3 Months</option>
          <option value="SIX_MONTHS">6 Months</option>
          <option value="YEAR">Year</option>
          <option value="TOTAL">All</option>
        </select>
      </div>
    </div>
  );
}
