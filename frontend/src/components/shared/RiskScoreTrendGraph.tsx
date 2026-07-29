"use client";

import { useEffect, useState } from "react";
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
  type Chart,
  type ChartOptions,
  type Plugin,
  type TooltipItem,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type RiskScorePoint = {
  calculated_at: string;
  score: number;
  classification: RiskLevel;
};

export type RiskThresholds = {
  low_max: number;
  medium_max: number;
};

type ChartTheme = {
  blue: string;
  navy: string;
  mist: string;
  body: string;
  border: string;
  card: string;
  font: string;
  safe: string;
  caution: string;
  threat: string;
};

const DEFAULT_THRESHOLDS: RiskThresholds = { low_max: 30, medium_max: 70 };

function daysAgoISO(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  d.setHours(9, 0, 0, 0);
  return d.toISOString();
}

const DEFAULT_HISTORY: RiskScorePoint[] = [
  { calculated_at: daysAgoISO(6), score: 22, classification: "LOW" },
  { calculated_at: daysAgoISO(5), score: 28, classification: "LOW" },
  { calculated_at: daysAgoISO(4), score: 45, classification: "MEDIUM" },
  { calculated_at: daysAgoISO(3), score: 38, classification: "HIGH" },
  { calculated_at: daysAgoISO(2), score: 52, classification: "MEDIUM" },
  { calculated_at: daysAgoISO(1), score: 63, classification: "MEDIUM" },
  { calculated_at: daysAgoISO(0), score: 81, classification: "HIGH" },
];

function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState({
    blue: "#3B5EDE",
    navy: "#1D2A5E",
    mist: "#D0D7E8",
    body: "#2E3A5C",
    border: "#D0D7E8",
    card: "#FFFFFF",
    font: "Inter, system-ui, sans-serif",
    safe: "#3DD68C",
    caution: "#F5A623",
    threat: "#F04444",
  });

  useEffect(() => {
    const styles = getComputedStyle(document.documentElement);
    const read = (name: string, fallback: string) =>
      styles.getPropertyValue(name)?.trim() || fallback;

    const animationFrameId = window.requestAnimationFrame(() => {
      setTheme({
        blue: read("--color-blue", "#3B5EDE"),
        navy: read("--color-navy", "#1D2A5E"),
        mist: read("--color-mist", "#D0D7E8"),
        body: read("--color-body", "#2E3A5C"),
        border: read("--border", "#D0D7E8"),
        card: read("--card", "#FFFFFF"),
        font: read("--font-sans", "Inter, system-ui, sans-serif"),
        safe: read("--color-safe", "#3DD68C"),
        caution: read("--color-caution", "#F5A623"),
        threat: read("--color-threat", "#F04444"),
      });
    });

    return () => window.cancelAnimationFrame(animationFrameId);
  }, []);

  return theme;
}

function thresholdBandsPlugin(
  lowMax: number,
  mediumMax: number,
  yMax: number,
  colors: any,
) {
  return {
    id: "thresholdBands",
    beforeDatasetsDraw(chart: any) {
      const { ctx, chartArea, scales } = chart;
      if (!chartArea) return;
      const y = scales.y;

      if (!y) return;

      const zones: [number, number, string][] = [
        [0, lowMax, colors.safe],
        [lowMax, mediumMax, colors.caution],
        [mediumMax, yMax, colors.threat],
      ];
      ctx.save();
      ctx.globalAlpha = 0.08;
      for (const [from, to, color] of zones) {
        const top = y.getPixelForValue(to);
        const bottom = y.getPixelForValue(from);
        ctx.fillStyle = color;
        ctx.fillRect(
          chartArea.left,
          top,
          chartArea.right - chartArea.left,
          bottom - top,
        );
      }
      ctx.restore();
    },
  };
}

type Props = {
  data?: RiskScorePoint[];
  thresholds?: RiskThresholds;
};

export function RiskScoreTrendGraph({
  data = DEFAULT_HISTORY,
  thresholds = DEFAULT_THRESHOLDS,
}: Props) {
  const theme = useChartTheme();

  const isOverride = (score: number, level: RiskLevel) =>
    level === "HIGH" && score <= thresholds.medium_max;
  const colorFor = (level: RiskLevel) =>
    level === "LOW"
      ? theme.safe
      : level === "MEDIUM"
        ? theme.caution
        : theme.threat;

  const maxScore = Math.max(...data.map((h) => h.score));
  const yMax = Math.max(thresholds.medium_max * 1.3, maxScore * 1.15);

  const rangeLabel =
    data.length === 0
      ? ""
      : `${new Date(data[0].calculated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })} – ${new Date(
          data[data.length - 1].calculated_at,
        ).toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;

  const chartData = {
    labels: data.map((h) =>
      new Date(h.calculated_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
    ),
    datasets: [
      {
        label: "Risk score",
        data: data.map((h) => h.score),
        borderColor: theme.blue,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: data.map((h) =>
          isOverride(h.score, h.classification) ? 7 : 4,
        ),
        pointHoverRadius: 8,
        pointBackgroundColor: data.map((h) => colorFor(h.classification)),
        pointBorderColor: data.map((h) =>
          isOverride(h.score, h.classification) ? theme.threat : theme.card,
        ),
        pointBorderWidth: data.map((h) =>
          isOverride(h.score, h.classification) ? 3 : 1.5,
        ),
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: "Neighbourhood risk score trend",
        align: "start" as const,
        color: theme.navy,
        font: { family: theme.font, size: 16, weight: "bold" },
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
        titleFont: { family: theme.font, weight: 600 },
        bodyFont: { family: theme.font },
        callbacks: {
          label: (ctx: TooltipItem<"line">) => {
            const point = data[ctx.dataIndex];
            const lines = [
              `Score: ${point.score}`,
              `Classification: ${point.classification}`,
            ];
            if (isOverride(point.score, point.classification))
              lines.push("Critical event override");
            return lines;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: theme.border },
        ticks: { color: theme.body, font: { family: theme.font, size: 11 } },
      },
      y: {
        beginAtZero: true,
        max: yMax,
        grid: { color: theme.mist },
        border: { display: false },
        ticks: {
          color: theme.body,
          font: { family: theme.font, size: 11 },
          precision: 0,
        },
      },
    },
  };

  const plugins = [
    thresholdBandsPlugin(
      thresholds.low_max,
      thresholds.medium_max,
      yMax,
      theme,
    ),
  ];

  return (
    <div
      className="rounded-lg p-6 w-full bg-card border"
      style={{ borderColor: "var(--border)", boxShadow: "var(--shadow-sm)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs" style={{ color: theme.body }}>
          {rangeLabel}
        </span>
        <div
          className="flex items-center gap-3 text-xs"
          style={{ color: theme.body }}
        >
          <span className="flex items-center gap-1">
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                background: theme.safe,
                display: "inline-block",
              }}
            />
            Low
          </span>
          <span className="flex items-center gap-1">
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                background: theme.caution,
                display: "inline-block",
              }}
            />
            Medium
          </span>
          <span className="flex items-center gap-1">
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                background: theme.threat,
                display: "inline-block",
              }}
            />
            High
          </span>
        </div>
      </div>
      <div className="h-72">
        <Line data={chartData} options={options} plugins={plugins} />
      </div>
    </div>
  );
}
