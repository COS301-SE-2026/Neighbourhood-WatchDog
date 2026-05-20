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

interface DialogBoxProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DialogBox({ open, onOpenChange }: DialogBoxProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <form>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Add camera</DialogTitle>
            <DialogDescription>
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
