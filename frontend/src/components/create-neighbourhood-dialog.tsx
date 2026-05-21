"use client"

import { CreateNeighbourhoodRes, NeighbourhoodResSchema, CreateNeighbourhoodReqSchema, NeighbourhoodRes } from "@/lib/validators/neighbourhood"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Spinner } from "./ui/spinner"
import { Field, FieldGroup } from "./ui/field"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { addNeighbourhood } from "@/lib/api/neighbourhood"

const PROPERTY_ID = "30000000-0000-0000-0000-000000000001"

interface CreatePropertyDialogAttributes {
  open: boolean
  onOpenChange: (open: boolean) => void
  onNeighbourhoodAdded: (property: NeighbourhoodRes) => void
}


export function CreateNeighbourhoodDialog(
  { open, onOpenChange, onNeighbourhoodAdded }: CreatePropertyDialogAttributes) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    setErrors({})
    setLoading(true)

    const formData = new FormData(e.currentTarget)
    const name = formData.get("name") as string
    const location = formData.get("location") as string

    const validatedStuff = CreateNeighbourhoodReqSchema.safeParse({
      name: name,
      location: location,
      property_id: PROPERTY_ID
    })

    if (!validatedStuff.success) {
      const newErrors: Record<string, string> = {}
      validatedStuff.error.issues.forEach((issue) => {
        const path = issue.path[0] as string
        newErrors[path] = issue.message
      })
      
      setErrors(newErrors)
      setLoading(false)
      return
    }

    try {
      const response = await addNeighbourhood(validatedStuff.data)
      onNeighbourhoodAdded(response)
      onOpenChange(false)
    } catch (error) {
      setErrors({ submit: "Failed to create neighbourhood" })
    } finally {
      setLoading(false)
    }
  }

  // TODO: refactor this dialogue to use the same component as the createpropertyone and just to pass in the fields that the user must enter
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm [font-family:var(--font-jetbrains-mono)]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {loading && <Spinner className="mr-2 h-4 w-4 animate-spin" />}
            {loading ? "Creating..." : "Create Neighbourhood"}
          </DialogTitle>
          <DialogDescription >
            Enter the details of your new neighbourhood
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          {errors.submit && (
            <p className="text-sm text-red-500 mb-4">{errors.submit}</p>
          )}
          <FieldGroup>
            <Field>
              <Label htmlFor="name-1">Neighbourhood Name</Label>
              <Input id="name-1" name="name" defaultValue="" placeholder="e.g., Westwood Heights" />
              {errors["name"] && (
                <p className="text-sm text-red-500 text-xs mt-0.5">{errors["name"]}</p>
              )}
            </Field>

            <Field>
              <Label htmlFor="location-1">Location</Label>
              <Input id="location-1" name="location" defaultValue="" placeholder="e.g., Johannesburg, Gauteng" />
              {errors["location"] && (
                <p className="text-sm text-red-500 text-xs mt-0.5">{errors["location"]}</p>
              )}
            </Field>
          </FieldGroup>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button type="submit" disabled={loading}>
              {loading && <Spinner className="mr-2 h-4 w-4 animate-spin" /> }
              {loading ? "Creating..." : "Create Neighbourhood"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}