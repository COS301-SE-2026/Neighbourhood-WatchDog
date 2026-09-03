"use client"

import { Button } from "@/components/ui/button"
import z from "zod"
import { Spinner } from "../ui/spinner"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

import { useState } from "react"
import { CreatePropertyReqSchema, PropertyRes } from "@/lib/validators/property"
import { AddressPicker, type SelectedAddress } from "./address-picker"
import { addProperty } from "@/lib/api/property"


interface CreatePropertyDialogAttributes {
  open: boolean
  onOpenChange: (open: boolean) => void
  onPropertyAdded: (property: PropertyRes) => void
}

export function CreatePropertyDialog({ open, onOpenChange, onPropertyAdded }: CreatePropertyDialogAttributes) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [selectedAddress, setSelectedAddress] = useState<SelectedAddress | null>(null);

  const handleSubmit = async (
      e: React.FormEvent<HTMLFormElement>,
  ) => {
      e.preventDefault();
      setErrors({});
      setLoading(true);

      const form = e.currentTarget;

      try {
          if (!selectedAddress) {
              setErrors({
                  address: "Please search for and select an address.",
              });
              return;
          }

          const validatedCreateProp =
              CreatePropertyReqSchema.safeParse({
                  address: selectedAddress.displayName,
                  property_type: "PRIVATE",
                  latitude: selectedAddress.latitude, 
                  longitude: selectedAddress.longitude
              });

          if (!validatedCreateProp.success) {
              setErrors({
                  address:
                      validatedCreateProp.error.issues[0]?.message ??
                      "Please select a valid address.",
              });
              return;
          }

          const createdProperty = await addProperty(
              validatedCreateProp.data,
          );

          onPropertyAdded(createdProperty);
          form.reset();
          setSelectedAddress(null);
          onOpenChange(false);
      } catch (error) {
          console.error("Failed to create property:", error);

          if (error instanceof z.ZodError) {
              const fieldErrors: Record<string, string> = {};

              error.issues.forEach((issue) => {
                  const path = issue.path.join(".");
                  fieldErrors[path] = issue.message;
              });

              setErrors(fieldErrors);
          } else {
              setErrors({
                  submit:
                      error instanceof Error
                          ? error.message
                          : "Failed to create property",
              });
          }
      } finally {
          setLoading(false);
      }
  };


  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-border bg-brand-abyss text-brand-frost sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold tracking-tight text-brand-frost">
            {loading ? "Creating..." : "Create Property"}
          </DialogTitle>
          <DialogDescription className="text-brand-ash">
            Search for and select the address of your property.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          {errors.submit && (
            <p className="mb-4 text-sm text-threat">{errors.submit}</p>
          )}
          
          <AddressPicker
              value={selectedAddress}
              onSelect={(address) => {
                  setSelectedAddress(address);

                  if (address) {
                      setErrors((currentErrors) => {
                          const nextErrors = { ...currentErrors };
                          delete nextErrors.address;
                          return nextErrors;
                      });
                  }
              }}
              error={errors.address}
          />


          <DialogFooter className="mt-6 border-t border-border bg-brand-abyss pt-4">
            <DialogClose asChild>
              <Button variant="outline" type="button" disabled={loading} className="border-border bg-brand-depth text-brand-frost hover:bg-brand-slate hover:text-brand-frost">Cancel</Button>
            </DialogClose>
            <Button type="submit" disabled={loading} className="bg-brand-green text-brand-void hover:bg-brand-green">
              {loading && <Spinner className="mr-2 size-4 animate-spin" /> }
              {loading ? "Creating..." : "Create Property"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}