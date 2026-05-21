"use client"

import { Button } from "@/components/ui/button"
import z from "zod"
import { Spinner } from "./ui/spinner"
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
import { Field, FieldGroup } from "./ui/field"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { CreatePropertyReq, AddressSchema, CreatePropertyReqSchema } from "@/lib/validators/property"


interface CreatePropertyDialogAttributes {
open: boolean
  onOpenChange: (open: boolean) => void
  onPropertyAdded: (property: CreatePropertyReq) => void //TODO make the zod thing for this so to avoid using any coz linter is gonna complain if I use any
}

export function CreatePropertyDialog({ open, onOpenChange, onPropertyAdded }: CreatePropertyDialogAttributes) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)

    const formData = new FormData(e.currentTarget)

    const address = {
      "address-line-1": formData.get("address-line-1") as string,
      "address-line-2": formData.get("address-line-1") as string,
      city: formData.get("city") as string,
      province: formData.get("province") as string,
      location: formData.get("location") as string
    }

    const property = "PRIVATE" 
    //TODO: consider whether to change hthis in the future. 
    // client said that we don't need to worry about public properties for now

    try {
      const validatedAddr = AddressSchema.parse(address)

      const addrValues = Object.values(validatedAddr).filter(value => value !== "") 
                                                // filter ^here is to remove the empty address line 2 that is optional
      const singleLineAdd = addrValues.join("\n")
      const validatedCreatePropSchema = CreatePropertyReqSchema.parse(singleLineAdd)

      onPropertyAdded(validatedCreatePropSchema)
      onOpenChange(false)
      e.currentTarget.reset()

    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {}
        error.issues.forEach((err) => {
          const path = err.path.join(".")
          fieldErrors[path] = err.message
        })
        setErrors(fieldErrors)
      }
    } finally {
      setLoading(false)
    }   

  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {loading && <Spinner className="mr-2 h-4 w-4 animate-spin" />}
            {loading ? "Creating..." : "Create Property"}            
          </DialogTitle>
          <DialogDescription >
            Enter the details of your property
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>

          <FieldGroup>
            <Field>
              <Label htmlFor="add-line-1">Address Line 1 (Street address)</Label>
              <Input id="add-line-1" name="address-line-1" defaultValue="" />
              {errors["address-line-1"] && (
                <p className="text-sm text-red-500 mt-1">{errors["address-line-1"]}</p>
              )}
            </Field>

            <Field>
              <Label htmlFor="add-line-2">Address Line 2 (Apartment, suite, unit, building etc.)</Label>
              <Input id="add-line-2" name="address-line-2" defaultValue="" />
              {errors["address-line-2"] && (
                <p className="text-sm text-red-500 mt-1">{errors["address-line-2"]}</p>
              )}
            </Field>

            <Field>
              <Label htmlFor="city-1">City</Label>
              <Input id="city-1" name="city" defaultValue="" />
              {errors["city"] && (
                <p className="text-sm text-red-500 mt-1">{errors["city"]}</p>
              )}
            </Field>

            <Field>
              <Label htmlFor="province-1">Province</Label>
              <select
                id="province-1"
                name="province"
                defaultValue="Gauteng"
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Select a province</option>
                <option value="Eastern Cape">Eastern Cape</option>
                <option value="Free State">Free State</option>
                <option value="Gauteng">Gauteng</option>
                <option value="KwaZulu-Natal">KwaZulu-Natal</option>
                <option value="Limpopo">Limpopo</option>
                <option value="Mpumalanga">Mpumalanga</option>
                <option value="Northern Cape">Northern Cape</option>
                <option value="North West">North West</option>
                <option value="Western Cape">Western Cape</option>
              </select>
              {errors["province"] && (
                <p className="text-sm text-red-500 mt-1">{errors["province"]}</p>
              )}
            </Field>

            <Field>
              <Label htmlFor="location-1">Location/Postal Code</Label>
              <Input id="location-1" name="location" defaultValue="" />
              {errors["location"] && (
                <p className="text-sm text-red-500 mt-1">{errors["location"]}</p>
              )}
            </Field>
            

          </FieldGroup>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button type="submit" disabled={loading}>
              {loading && <Spinner className="mr-2 h-4 w-4 animate-spin" /> }
              {loading ? "Creating..." : "Create Property"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}