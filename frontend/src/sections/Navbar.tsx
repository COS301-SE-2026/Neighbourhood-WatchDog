"use-client";

import Image from "next/image"
import logoImage from "@/assets/images/logo-mark-only.svg"
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { twMerge } from "tailwind-merge";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
const navLinks = [
    {label: "Home", href: "#"},
    {label: "Features", href: "#features"},
    {label: "Integrations", href: "#integrations"},
    {label: "FAQs", href: "#faqs"}

]

export default function Navbar() {

    const [isOpen, setIsOpen] = useState(false)
    return (
        <>
            <section className="py-4 flex justify-center lg:py-8 fixed w-full top-0 z-50">
                    <div className="container max-w-5xl px-4 lg:px-0">
                        <div className="border border-white/15 rounded-[27px] md:rounded-full bg-neutral-950/70 backdrop-blur">
                            <div className="grid grid-cols-2 lg:grid-cols-3   p-2 px-4 md:pr-2 items-center ">
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
                                        onClick={() => setIsOpen(!isOpen)}
                                    >
                                        <line x1="3" y1="6" x2="21" y2="6" className={twMerge("origin-left transition",isOpen && "rotate-45 -translate-y-1")}></line>
                                        <line x1="3" y1="12" x2="21" y2="12" className={twMerge("transition", isOpen && "opacity-0")}></line>
                                        <line x1="3" y1="18" x2="21" y2="18" className={twMerge("origin-left transition",isOpen && "-rotate-45 translate-y-1")}></line>
                                    </svg>
                                    <Button asChild variant="ghost" className="hidden md:inline-flex border border-white h-10 rounded-full px-6 font-medium items-center"><Link href="auth/login">Log In</Link></Button>
                                    <Button asChild variant="default" className="hidden md:inline-flex h-10 rounded-full px-6 font-medium items-center"><Link href="auth/signup">Sign Up</Link></Button>
                                </div>
                            </div>
                            <AnimatePresence>
                                {isOpen && (
                                    <motion.div initial={{height: 0}} animate={{height: "auto"}} exit={{height: 0}} className="overflow-hidden">
                                        <div className="flex flex-col items-center gap-4 py-4 ">
                                            {navLinks.map(link => (
                                                <a
                                                    href={link.href}
                                                    key={link.label}
                                                    className="py-2"
                                                >
                                                    {link.label}
                                                </a>
                                            ))}
                                            <Button asChild variant="ghost" className=" md:inline-flex border border-white h-10 rounded-full px-6 font-medium items-center"><Link href="auth/login">Log In</Link></Button>
                                            <Button asChild variant="default" className=" md:inline-flex h-10 rounded-full px-6 font-medium items-center"><Link href="auth/signup">Sign Up</Link></Button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </section>

                <div className="pb-[86px] md:pb-[96px] lg:pb-[130px]">

                </div>
        </>
    );
}