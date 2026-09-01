"use client"

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { useState} from "react"
import {MoreVertical, Edit, Trash} from "lucide-react"
import {Button} from "@/components/ui/button"
import RemoveCamera from "./remove-camera-card"
import { EditCamera } from "./edit-camera-card"
import { deleteCamera as apiDeleteCamera, editCamera as apiEditCamera } from "@/lib/api/camera"
interface CameraDropdownProp {
    camera_id: string
    camera_name: string
    camera_location: string
    camera_visibility: "PUBLIC" | "PRIVATE" | "NEIGHBOURHOOD"
    camera_enabled: boolean
    onDeleted: (cameraId: string) => void
}
export function CameraDropdown({camera_id, camera_name, camera_location, camera_visibility, camera_enabled, onDeleted}: Readonly<CameraDropdownProp>) {

    const [isDelete, setDelete] = useState(false);
    const [isEdit, setEdit] = useState(false);
    
    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8 p-0">
                        <MoreVertical/> 
                    </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="cursor-pointer" onSelect={() => {
                            setEdit(true)
                        }}>
                        <Edit className="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive cursor-pointer" onSelect={(e) => {
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
                        console.log("camera with id ", camera_id, " to be deleted")
                        try {
                            await apiDeleteCamera(camera_id)
                            onDeleted(camera_id)
                            setDelete(false)
                            //going to add a toast notification
                        } catch(error) {
                            console.error("Failed to delete camera:", error)
                            //going add a toast notification here too
                        }

                    }}
                />
            )}

            {isEdit && (
                <EditCamera 
                    open={isEdit}
                    name={camera_name}
                    location={camera_location}
                    visibility={camera_visibility}
                    enabled={camera_enabled}
                    onOpenChange={setEdit}
                    onConfirm={async (data) => {
                        console.log("camera with id ", camera_id, " to be edited")
                        try {
                            await apiEditCamera(camera_id, data)
                            setEdit(false)
                            //going to add a toast notification
                        } catch(error) {
                            console.error("Failed to edit camera:", error)
                            //going add a toast notification here too
                        }

                    }}
                />
            )}
        </>
    )
}

export default CameraDropdown;