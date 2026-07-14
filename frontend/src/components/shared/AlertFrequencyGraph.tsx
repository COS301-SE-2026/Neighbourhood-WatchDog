"use client"

import React, { use, useEffect, useState } from 'react';
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
import { NumberInPeriod, TimeIntervalsEnum, TimePeriod } from '@/lib/validators/alert';
import { fetchAlertFrequencyData } from '@/lib/api/alert';
import { useAlertFrequencyMetrics } from '@/hooks/use-alert-metrics';
import { count } from 'console';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface useAlertFrequencyMetricsProps{
    neighbourhoodId: string
    timeInt?: TimeIntervalsEnum
    timePer?: TimePeriod
}

export function AlertFrequencyGraph({
	neighbourhoodId,
	timeInt,
	timePer
}: useAlertFrequencyMetricsProps){

	const [timeInterval, setTimeInterval] = useState<TimeIntervalsEnum>("DAILY")
	const [timePeriod, setTimePeriod] = useState<TimePeriod>("MONTH")

	const {metrics, loading, error, refetch} = useAlertFrequencyMetrics(neighbourhoodId, timeInt, timePer)

	const dates = metrics?.period
	const count = metrics?.count

	return (
		<div>
			{dates && count && <Line
				data={{
					labels: dates,
					datasets: [
						{
							label: 'Count',
							data: count
							}
					]
				}}>

			</Line>}
		</div>
	)
}