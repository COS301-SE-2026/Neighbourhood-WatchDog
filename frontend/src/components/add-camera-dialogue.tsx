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
import { useCameras } from "@/hooks/use-camera"
import { CameraInput, Camera, cameraInputSchema } from "@/lib/validators/camera"
import { useState } from "react"

interface DialogBoxProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCameraAdded: (camera: any) => void
  propertyId: string
}

export function AddCameraDialogBox({ open, onOpenChange, onCameraAdded, propertyId }: DialogBoxProps) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setErrors({})
  
    const formData = new FormData(e.currentTarget)
    
    const rtsp_url = formData.get("rtsp_url") as string
    const location = formData.get("location") as string
    const visibility = formData.get("visibility") as "PRIVATE" | "PUBLIC"

    const rawData: CameraInput = {
      rtsp_url,
      location,
      visibility,
      property_id: propertyId
    }

    const result = cameraInputSchema.safeParse(rawData)
    if (!result.success){
      // TODO: Add the validation errors to tell user whats wrong
      setErrors({...errors, validate: "Invalid data"})
      return
    }

    //if the code gets here it means that the validation has passed.
    const data: CameraInput = result.data
    try {  
      setLoading(true)
      await onCameraAdded(result.data) 
      onOpenChange(false)  // Close dialog on success
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to add camera"
      setErrors({ submit: message })
    } finally {
      setLoading(false)
    }
  }


  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Add camera</DialogTitle>
          <DialogDescription >
            Enter the details of your camera.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
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
                defaultValue="PRIVATE"
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="PUBLIC">Public</option>
                <option value="PRIVATE">Private</option>
                <option value="RESTRICTED">RESTRICTED</option>
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
