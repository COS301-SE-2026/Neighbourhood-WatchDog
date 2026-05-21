import {z } from "zod"

export const PropertyTypeEnum = z.enum([
  "PRIVATE",
  "PUBLIC",
]);

export const CreatePropertyReqSchema = z.object({
  address: z
    .string({ message: "Address is required" })
    .nonempty("Address cannot be empty"),
  propertyType: PropertyTypeEnum,
});

export const PropertyResSchema = z.object({
  userId: z
    .uuid("User ID must be a valid UUID"),
  neighbourhoodId: z
    .uuid("Neighbourhood ID must be a valid UUID")
    .nullable(),
  address: z
    .string({ message: "Address is required" })
    .nonempty("Address cannot be empty"),
  propertyType: z
    .string({ message: "Property type is required" })
    .nonempty("Property type cannot be empty"),
  createdAt: z
    .coerce
    .date()
    .default(() => new Date()),
});

export const CreatePropertyResSchema = z.object({
  status: z
    .number({ message: "Status code is required" })
    .int("Status must be an integer"),
  message: z
    .string({ message: "Message must be a string" })
    .nullable()
    .optional(),
  data: PropertyResSchema.nullable().optional(),
});

const SOUTH_AFRICAN_PROVINCES = [
  "Eastern Cape",
  "Free State",
  "Gauteng",
  "KwaZulu-Natal",
  "Limpopo",
  "Mpumalanga",
  "Northern Cape",
  "North West",
  "Western Cape",
] as const;

type SouthAfricanProvince = typeof SOUTH_AFRICAN_PROVINCES[number];

export const AddressSchema = z.object({
  "address-line-1": z
    .string()
    .min(5, "Address line 1 must be at least 5 characters")
    .max(100, "Address line 1 must be less than 100 characters"),
  
  "address-line-2": z
    .string()
    .max(100, "Address line 2 must be less than 100 characters")
    .optional()
    .or(z.literal("")),
  
  city: z
    .string()
    .min(2, "City must be at least 2 characters")
    .max(50, "City must be less than 50 characters"),
  
  province: z.enum(SOUTH_AFRICAN_PROVINCES as readonly [SouthAfricanProvince, ...SouthAfricanProvince[]]),
  
  zipCode: z.string().length(4).regex(/^\d+$/, "Must have 4 characters and consist of strings")
});

export type Address = z.infer<typeof AddressSchema>;

// Types
export type CreatePropertyReq = z.infer<typeof CreatePropertyReqSchema>;
export type PropertyRes = z.infer<typeof PropertyResSchema>;
export type CreatePropertyRes = z.infer<typeof CreatePropertyResSchema>;
export type PropertyType = z.infer<typeof PropertyTypeEnum>;