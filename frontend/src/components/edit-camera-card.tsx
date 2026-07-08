"use client"

import { 
    Dialog, 
    DialogClose, 
    DialogContent, 
    DialogDescription, 
    DialogFooter, 
    DialogHeader, 
    DialogTitle 
} from "@/components/ui/dialog"
import {Field, FieldGroup} from "@/components/ui/field"
import {Input} from "@/components/ui/input"
import {Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select"
import {Switch} from "@/components/ui/switch"
import {Button} from "@/components/ui/button"
import {Label} from "@/components/ui/label"
import { CameraEditInput } from "@/lib/validators/camera"
import { useState } from "react"
import { validateHeaderName } from "http"

interface EditCameraProps {
    open: boolean
    name: string
    onOpenChange: (open: boolean) => void
    onConfirm?: (data: CameraEditInput) => void

}



export function EditCamera({ open, name, onOpenChange, onConfirm }: Readonly<EditCameraProps>) {


    const [visibility, setVisibility] = useState<"PRIVATE" | "PUBLIC" | "NEIGHBOURHOOD">("PUBLIC");
    const [enabled, setEnabled] = useState(true)
    function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault()

        const formData = new FormData(event.currentTarget)

        onConfirm?.({
        name: String(formData.get("name") || ""),
        location: String(formData.get("location") || ""),
        visibility,
        enabled,
        })
    }


    return (

        <Dialog open={open} onOpenChange={onOpenChange}>
            <form onSubmit={handleSubmit}>
                <DialogContent className="sm:max-w-sm">
                <DialogHeader>
                    <DialogTitle>Edit camera</DialogTitle>
                    <DialogDescription>
                    Update the camera details and save your changes.
                    </DialogDescription>
                </DialogHeader>

                <FieldGroup>
                    <Field>
                    <Label htmlFor="name">Name</Label>
                    <Input id="name" name="name" defaultValue={name} />
                    </Field>

                    <Field>
                    <Label htmlFor="location">Location</Label>
                    <Input id="location" name="location" defaultValue="" />
                    </Field>

                    <Field>
                    <Label htmlFor="visibility">Visibility</Label>
                    <Select value={visibility} onValueChange={(value) => setVisibility(value as "PRIVATE" | "PUBLIC" | "NEIGHBOURHOOD")}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select visibility"/>
                        </SelectTrigger>

                        <SelectContent>
                            <SelectGroup>
                                <SelectItem value="PRIVATE">Private</SelectItem>
                                <SelectItem value="PUBLIC">Public</SelectItem>
                                <SelectItem value="NEIGHBOURHOOD">Neighbourhood</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                    
                    </Field>

                    <Field>
                        <Label htmlFor="enabled">Enabled</Label>
                        <Switch id="enabled" checked={enabled} onCheckedChange={setEnabled} />
                    </Field>
                </FieldGroup>

                <DialogFooter>
                    <DialogClose asChild>
                    <Button type="button" variant="outline">Cancel</Button>
                    </DialogClose>
                    <Button type="submit">Save changes</Button>
                </DialogFooter>
                </DialogContent>
            </form>
        </Dialog>
    )
}