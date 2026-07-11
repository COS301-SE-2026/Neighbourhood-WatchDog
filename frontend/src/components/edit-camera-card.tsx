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
import {useState } from "react"

interface EditCameraProps {
    open: boolean
    name: string
    location: string
    visibility: "PUBLIC" | "PRIVATE" | "NEIGHBOURHOOD"
    enabled: boolean
    onOpenChange: (open: boolean) => void
    onConfirm?: (data: CameraEditInput) => void

}



export function EditCamera({ 
    open, 
    name, 
    location,
    visibility: initialVisibility,
    enabled: initialEnabled,
    onOpenChange, 
    onConfirm }: Readonly<EditCameraProps>) {


    const [visibility, setVisibility] = useState(initialVisibility);
    const [enabled, setEnabled] = useState(initialEnabled)
    const [nameValue, setNameValue] = useState(name)
    function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault()

        const formData = new FormData(event.currentTarget)

        onConfirm?.({
        name: nameValue,
        location: typeof formData.get("location") === "string" ? (formData.get("location") as string) : "",
        visibility,
        enabled,
        })
    }


    return (

        <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent className="sm:max-w-sm">
                    <form onSubmit={handleSubmit}>
                        <DialogHeader>
                            <DialogTitle>Edit camera</DialogTitle>
                            <DialogDescription>
                            Update the camera details and save your changes.
                            </DialogDescription>
                        </DialogHeader>

                        <FieldGroup>
                            <Field>
                            <Label htmlFor="name">Name</Label>
                            <Input id="name" name="name" defaultValue={name} onChange={(e) => setNameValue(e.target.value)}/>
                            </Field>

                            <Field>
                            <Label htmlFor="location">Location</Label>
                            <Input id="location" name="location" defaultValue={location} />
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
                    </form>
                </DialogContent>
        </Dialog>
    )
}