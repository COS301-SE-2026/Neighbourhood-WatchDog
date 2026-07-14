import { z } from "zod";

export const TimeIntervalsEnum = z.enum(["DAILY", "MONTHLY", "YEARLY"])

export const TimePeriod = z.enum([
    "WEEK",
    "MONTH",
    "THREE_MONTHS",
    "SIX_MONTHS",
    "YEAR",
    "TOTAL",
])

export const NumberInPeriod = z.object({
    period: z.coerce.date(),
    count: z.number().int(),
})

export const AlertFrequencyMetricsRes = z.object({
    status: z.number().int(),
    message: z.string().nullable().optional(),
    data: z.array(NumberInPeriod).nullable().optional(),
})

export type TimePeriod = z.infer<typeof TimePeriod>
export type TimeIntervalsEnum = z.infer<typeof TimeIntervalsEnum>
export type NumberInPeriod = z.infer<typeof NumberInPeriod>
export type AlertFrequencyMetricsRes = z.infer<typeof AlertFrequencyMetricsRes>