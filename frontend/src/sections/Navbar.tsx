import Image from "next/image"
import logoImage from "@/assets/images/logo-mark-only.svg"
import { Button } from "@/components/ui/button";

const navLinks = [
    {label: "Home", href: "#"},
    {label: "Features", href: "#features"},
    {label: "Integrations", href: "#integrations"},
    {label: "FAQs", href: "#faqs"}

]

export default function Navbar() {
    return <section className="py-4 flex justify-center lg:py-8">
            <div className="container max-w-5xl">
                <div className="grid grid-cols-2 lg:grid-cols-3 border border-white/15 rounded-full p-2 px-4 md:pr-2 items-center">
                    <div className="flex items-center gap-2">
                        <Image src={logoImage} alt={"Neighbourhood Watchdog logo"} className="h-9 w-auto ml-2"/>
                        <span className="font-bold text-lg">Watchdog</span>
                    </div>

                    <div className="lg:flex justify-center items-center gap-8 hidden">
                        {navLinks.map(link => (
                            <a href={link.href} key={link.label}>
                                {link.label}
                            </a>
                        ))}
                    </div>

                    <div className="flex items-center justify-end gap-2">
                        <svg 
                            xmlns="http://www.w3.org/2000/svg" 
                            width="24" height="24" viewBox="0 0 24 24" 
                            fill="none" stroke="currentColor" 
                            stroke-width="2" 
                            stroke-linecap="round" 
                            stroke-linejoin="round" 
                            className="feather feather-menu md:hidden"
                        >
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                        <Button variant="ghost" className="hidden md:inline-flex border border-white h-10 rounded-full px-6 font-medium items-center">Log In</Button>
                        <Button variant="default" className="hidden md:inline-flex h-10 rounded-full px-6 font-medium items-center">Sign Up</Button>
                    </div>
                </div>
            </div>
        </section>;
}