import { Moon, User } from "lucide-react";
import Link from "next/link";
import { AvatarFallback, Avatar } from "@/components/ui/avatar";

const Navbar = () => {
    return (
        <nav className="p-4 flex items-center justify-between">
            collapseButton
            <div className="flex items-center gap-4">
                <Link href="">Dashboard</Link>
                <Moon/>
                <Avatar>
                <AvatarFallback className="bg-muted text-muted-foreground">
                    <User className="size-4" />
                </AvatarFallback>
                </Avatar>
            </div>
        </nav>
    )
}

export default Navbar;