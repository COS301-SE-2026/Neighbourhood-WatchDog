"use client"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button";

interface RemoveCameraProps {
  open: boolean
  name: string
  onOpenChange: (open: boolean) => void
  onConfirm?: () => void
}


export function RemoveCamera({ open, name, onOpenChange, onConfirm }: RemoveCameraProps) {

    return (
        <AlertDialog open={open} onOpenChange={onOpenChange}>
            {/* <AlertDialogTrigger asChild>
                <Button variant="outline">Show Dialog</Button>
            </AlertDialogTrigger> */}

            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Remove camera?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This will permenantly remove <strong>{name}</strong> from your account. This action cannot be undone.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={onConfirm}>Continue</AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}

export default RemoveCamera;