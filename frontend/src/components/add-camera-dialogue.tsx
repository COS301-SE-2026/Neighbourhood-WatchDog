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

import { Field, FieldGroup } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CameraInput, Camera } from "@/lib/validators/camera"
import { useState } from "react"

interface DialogBoxProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCameraAdded: (camera: any) => void
  propertyId: string
}

export function DialogBox({ open, onOpenChange, onCameraAdded, propertyId }: DialogBoxProps) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setErrors({})
  }

  const formData = new FormData(e.currentTarget)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <form onSubmit={handleSubmit}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold">Add camera</DialogTitle>
            <DialogDescription >
              Enter the details of your camera.
            </DialogDescription>
          </DialogHeader>
          <FieldGroup>
            <Field>
              <Label htmlFor="name-1">Name</Label>
              <Input id="name-1" name="name" defaultValue="Camera 1" />
            </Field>
            <Field>
              <Label htmlFor="location-1">Location</Label>
              <Input id="location-1" name="location" defaultValue="Backyard" />
            </Field>
            <Field>
              <Label htmlFor="rtsp-1">RTSP URL</Label>
              <Input id="rtsp-1" name="rtsp_url" defaultValue="rtsp://" />
            </Field>
            <Field>
              <Label htmlFor="visibility-1">Visibility</Label>
              <select
                id="visibility-1"
                name="visibility"
                defaultValue="private"
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
        </DialogContent>
      </form>
    </Dialog>
  )
}
