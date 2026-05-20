"use client"

import { Button } from "@/components/ui/button"

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
import { CreatePropertyReqSchema } from "@/lib/validators/property"


interface CreatePropertyDialogAttributes {
open: boolean
  onOpenChange: (open: boolean) => void
  onPropertyAdded: (property) => void //TODO make the zod thing for this so to avoid using any coz linter is gonna complain if I use any
}

export function CreatePropertyDialog({ open, onOpenChange, onPropertyAdded }: CreatePropertyDialogAttributes) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Create Property</DialogTitle>
          <DialogDescription >
            Enter the details of your property
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
            <Field>
              <Label htmlFor="location-1">Property Address</Label>
              <Input id="location-1" name="location" defaultValue="Backyard" />
            </Field>
            <Field>
              <Label htmlFor="rtsp-1">Location</Label>
              <Input id="rtsp-1" name="rtsp_url" defaultValue="rtsp://" />
            </Field>
            <Field>
              <Label htmlFor="visibility-1">Visibility</Label>
              <select
                id="visibility-1"
                name="visibility"
                defaultValue="PRIVATE"
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="PUBLIC">Public</option>
                <option value="PRIVATE">Private</option>
              </select>
            </Field>
          </FieldGroup>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button type="submit">Add camera</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}