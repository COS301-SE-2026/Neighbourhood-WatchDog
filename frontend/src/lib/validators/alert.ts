import { z } from "zod";

export const TimeIntervalsEnum = z.enum([
    "DAILY",
    "MONTHLY",
    "YEARLY"
])

export const TimePeriod = z.enum([
    "WEEK",
    "MONTH",
    "THREE_MONTHS",
    "SIX_MONTHS",
    "YEAR",
    "TOTAL",
])

export const CriticalDetectionTypeSchema = z.enum([
  "WEAPON_DETECTED",
  "FALL_DETECTED"
]);

export const CriticalAlertStatusSchema = z.enum([
  "OPEN",
  "ACKNOWLEDGED",
  "RESOLVED"
]);

const DatabaseUuidSchema = z
  .string()
  .regex(
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    "Invalid UUID format",
  );



export const NumberInPeriod = z.object({
    period: z.coerce.date().array(),
    count: z.number().int().array(),
})

export const AlertFrequencyMetricsRes = z.object({
    status: z.number().int(),
    message: z.string().nullable().optional(),
    data: NumberInPeriod.nullable().optional(),
})

export const CriticalAlertBaseSchema = z.object({
  id: DatabaseUuidSchema,
  camera_id: DatabaseUuidSchema,
  camera_name: z.string(),
  neighbourhood_id: DatabaseUuidSchema,
  detection_type: CriticalDetectionTypeSchema,
  status: CriticalAlertStatusSchema,
  created_at: z.string().datetime({ offset: true }),
  property_id: DatabaseUuidSchema,
  property_address: z.string(),
  thumbnail_url: z.string().nullable().optional()
});

export const CriticalAlertMapItemSchema =
  CriticalAlertBaseSchema.extend({
    latitude: z.number().finite().min(-90).max(90),
    longitude: z.number().finite().min(-180).max(180)
  });

export const UnlocatedCriticalAlertItemSchema =
  CriticalAlertBaseSchema.extend({
    latitude: z.number().finite().min(-90).max(90).nullable(),
    longitude: z.number().finite().min(-180).max(180).nullable(),
  }).refine(
    (alert) =>
      alert.latitude === null ||
      alert.longitude === null,
    {
      message:
        "An unlocated alert must have a missing coordinate",
    },
  );

export const CriticalAlertMapDataSchema = z.object({
  alerts: z.array(CriticalAlertMapItemSchema),
  last_updated: z.string().datetime({ offset: true })
});

export const CriticalAlertMapResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
  data: CriticalAlertMapDataSchema
});

export const UnlocatedCriticalAlertsDataSchema = z.object({
  alerts: z.array(UnlocatedCriticalAlertItemSchema),
  last_updated: z.string().datetime({ offset: true })
});

export const UnlocatedCriticalAlertsResSchema = z.object({
  status: z.number().int(),
  message: z.string().nullable().optional(),
  data: UnlocatedCriticalAlertsDataSchema
})

export const CriticalAlertMapCacheSchema =
  z.object({
    version: z.literal(1),
    mapped_alerts: z.array(
      CriticalAlertMapItemSchema,
    ),
    unlocated_alerts: z.array(
      UnlocatedCriticalAlertItemSchema,
    ),
    last_updated: z
      .string()
      .datetime({ offset: true }),
    cached_at: z
      .string()
      .datetime({ offset: true }),
  });



export type TimePeriod = z.infer<typeof TimePeriod>
export type TimeIntervalsEnum = z.infer<typeof TimeIntervalsEnum>
export type NumberInPeriod = z.infer<typeof NumberInPeriod>
export type AlertFrequencyMetricsRes = z.infer<typeof AlertFrequencyMetricsRes>
export type CriticalDetectionType = z.infer<typeof CriticalDetectionTypeSchema>;
export type CriticalAlertStatus = z.infer<typeof CriticalAlertStatusSchema>;
export type CriticalAlertMapItem = z.infer<typeof CriticalAlertMapItemSchema>;
export type UnlocatedCriticalAlertItem = z.infer<typeof UnlocatedCriticalAlertItemSchema>;
export type CriticalAlertMapRes = z.infer<typeof CriticalAlertMapResSchema>;
export type UnlocatedCriticalAlertsRes = z.infer<typeof UnlocatedCriticalAlertsResSchema>;
export type CriticalAlertMapCache = z.infer<typeof CriticalAlertMapCacheSchema>;
