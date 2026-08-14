"use client"

import Link from "next/link";
import { useState } from "react";
import {
    ArrowLeft,
    Check,
    MapPin,
} from "lucide-react";

export default function NeighbourhoodSetupPage() {


    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="max-w-full">
                <Link href="/dashboard-v2" className="inline-flex items-center gap-2 text-sm text-white/45 transition-colors hover:text-white">
                    <ArrowLeft className="size-4" />
                    Back to property
                </Link>

                <header className="mt-8 border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">
                        Neighbourhood setup
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                        Create a neighbourhood
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
                        Start a neighbourhood from this property. You can add 
                        neighbouring properties and residents after setup.
                    </p>
                </header>

            </div>
        </main>
    )
}