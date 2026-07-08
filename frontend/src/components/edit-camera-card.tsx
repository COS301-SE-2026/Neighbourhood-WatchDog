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
import {Select} from "@/components/ui/select"
import {Switch} from "@/components/ui/switch"
import {Button} from "@/components/ui/button"
import {Label} from "@/components/ui/label"
import { CameraEditInput } from "@/lib/validators/camera"

interface EditCameraProps {
    open: boolean
    name: string
    onOpenChange: (open: boolean) => void
    onConfirm?: (data: CameraEditInput) => void

}
export function EditCamera({ open, name, onOpenChange, onConfirm }: Readonly<EditCameraProps>) {
    return (
        <></>
    )
}