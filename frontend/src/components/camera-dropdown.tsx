"use client"

import {
  DropdownMenu,
  DropdownMenuPortal,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu"
import { useState, useEffect } from "react"
import {MoreVertical, Edit, Trash} from "lucide-react"
import {Button} from "@/components/ui/button"
import RemoveCamera from "./remove-camera-card"
import { deleteCamera as apiDeleteCamera } from "@/lib/api/camera"
import { id } from "zod/locales"
interface CameraDropdownProp {
    camera_id: string
    camera_name: string
}
export function CameraDropdown({camera_id, camera_name}: CameraDropdownProp) {

    const [isEdit, setEdit] = useState(false);
    const [isDelete, setDelete] = useState(false);

    
    return (
        <div onClick={(e) => e.stopPropagation()}>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8 p-0">
                        <MoreVertical/> 
                    </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="cursor-pointer" onClick={() => {console.log("Camera with id", camera_id)}}>
                        <Edit className="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive cursor-pointer" onClick={(e) => {
                        e.stopPropagation()
                        setDelete(true)
                        }}>
                        <Trash className="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            {isDelete && (
                <RemoveCamera 
                    open={isDelete}
                    name={camera_name}
                    onOpenChange={setDelete}
                    onConfirm={async () => {
                        // will add the logic here
                        console.log("camera with id ", camera_id, " to be deleted")
                        setDelete(false)
                        try {
                            await apiDeleteCamera(camera_id)
                            setDelete(false)
                            //going to add a toast notification
                        } catch(error) {
                            console.error("Failed to delete camera:", error)
                            //going add a toast notification here too
                        }

                    }}
                />
            )}
        </div>
    )
}

export default CameraDropdown;