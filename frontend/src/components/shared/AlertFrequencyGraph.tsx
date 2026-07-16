"use client"

import { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { TimeIntervalsEnum, TimePeriod } from '@/lib/validators/alert';
import { useAlertFrequencyMetrics } from '@/hooks/use-alert-metrics';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface AlertFrequencyMetricsProps{
    neighbourhoodId: string
    timeInt?: TimeIntervalsEnum
    timePer?: TimePeriod
}

function useChartTheme(){
	const [theme, setTheme] = useState({
		blue: "#3B5EDE",
		sky: "#5B8DEF",
		navy: "#1D2A5E",
		mist: "#D0D7E8",
		body: "#2E3A5C",
		card: "#FFFFFF",
		border: "#D0D7E8",
		font: "Inter, system-ui, sans-serif",
	})

	useEffect(() => {
		const styles = getComputedStyle(document.documentElement)
		const read = (name: string, fallback: string) => 
			styles.getPropertyValue(name)?.trim() || fallback

		setTheme({
			blue: read("--color-blue", "#3B5EDE"),
			sky: read("--color-sky", "#5B8DEF"),
			navy: read("--color-navy", "#1D2A5E"),
			mist: read("--color-mist", "#D0D7E8"),
			body: read("--color-body", "#2E3A5C"),
			card: read("--card", "#FFFFFF"),
			border: read("--border", "#D0D7E8"),
			font: read("--font-sans", "Inter, system-ui, sans-serif"),
		})
	}, [])

	return theme
}

export function AlertFrequencyGraph({
	neighbourhoodId,
	timeInt,
	timePer
}: AlertFrequencyMetricsProps){

	const [timeInterval, setTimeInterval] = useState<TimeIntervalsEnum>("DAILY")
	const [timePeriod, setTimePeriod] = useState<TimePeriod>("MONTH")

	const {metrics, loading, error, refetch} = useAlertFrequencyMetrics(
		neighbourhoodId,
		timeInt,
		timePer
	)

	const theme = useChartTheme();

	const dates = metrics?.period
	const counts = metrics?.count

	const chartData = useMemo(() => {
		if (!dates || !counts) return null

		return {
			labels: dates.map((d) => 
				new Date(d).toLocaleDateString(undefined, {month: "short", day: "numeric"})
			),
			datasets: [
				{
					label: "Alerts",
					data: counts,
					borderColor: theme.blue,
					backgroundColor: (context: any) => {
						const chart = context.chart
						const { ctx, chartArea } = chart
						if (!chartArea) return theme.sky
						const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
						gradient.addColorStop(0, `${theme.blue}33`)
						gradient.addColorStop(1, `${theme.blue}00`) 
						return gradient
					},
					fill: true,
					tension: 0.35,
					borderWidth: 2,
					pointRadius: 3,
					pointHoverRadius: 5,
					pointBackgroundColor: theme.blue,
					pointBorderColor: "#FFFFFF",
					pointBorderWidth: 1.5,
				},
			],
		}
	}, [dates, counts, theme])

	const options = useMemo(() => ({
		responsive: true,
		maintainAspectRatio: false,
		interaction: {mode: "index" as const, intersect: false},
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
				backgroundColor: "#FFFFFF",
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
				ticks: { color: theme.body, font: { family: theme.font, size: 11 } },
			},
			y: {
				beginAtZero: true,
				grid: { color: theme.mist },
				border: { display: false },
				ticks: {
					color: theme.body,
					font: { family: theme.font, size: 11 },
					precision: 0,
				}
			}
		}
	}), [theme])

	return (
		<div
      className="rounded-lg p-6 w-3/4 bg-card border"
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
    </div>
	)
}