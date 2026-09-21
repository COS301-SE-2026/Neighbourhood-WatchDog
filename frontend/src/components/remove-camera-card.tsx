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
} from "@/components/ui/alert-dialog"
import { LoaderCircle } from "lucide-react"

interface RemoveCameraProps {
  isDeleting?: boolean
  open: boolean
  name: string
  onOpenChange: (open: boolean) => void
  onConfirm?: () => void | Promise<void>
}


export function RemoveCamera({ isDeleting, open, name, onOpenChange, onConfirm }: Readonly<RemoveCameraProps>) {

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
                    <AlertDialogAction 
											disabled={isDeleting}
											onClick={(e) => {
													e.preventDefault()
													onConfirm?.()
											}}
                    >
											{isDeleting ? <LoaderCircle className="size-4 animate-spin"/> : "Continue"}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}

export default RemoveCamera;