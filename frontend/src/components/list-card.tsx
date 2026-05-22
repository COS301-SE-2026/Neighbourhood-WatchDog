"use client"

import { Card } from "@/components/ui/card"
import { Trash2 } from "lucide-react"

interface ListCardProps {
  title: string
  items: Array<{ id: string; name: string }>
  onAdd: () => void // TODO: Change this after demo 1
  onDelete: (id: string) => void
}

export function ListCard({ title, items, onAdd, onDelete }: ListCardProps){
  return (
    <Card className="!bg-navy text-black rounded-lg p-5">
      <h2 className="text-xl font-bold">{title}</h2>

      {/** creating the list of whatever it may be */}
      <div className="space-y-2">
        { items.map((item) => (
          <div key={item.id} className="flex justify-between items-center border-1 p-2 rounded-full">
            <span>{item.name}</span>
            <button onClick={() => onDelete(item.id)}>
              <Trash2 className="h-4 w-4 text-black"/>
            </button>
          </div>
        ))}
      </div>

      <button onClick={onAdd} className="bg-blue-500 text-navy rounded-full p-2 ">
        {/* <Plus className="h-4 w-4"/> */}
        <p>Add</p>
      </button>
    </Card>
  )
}