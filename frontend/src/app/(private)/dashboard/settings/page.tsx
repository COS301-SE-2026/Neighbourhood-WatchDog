"use client";

import { User as UserIcon } from "lucide-react";

export default function SettingsPage() {
    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="max-w-full">
                <header className="border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">Settings</p>
                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                        Account settings
                    </h1>
                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
                        Manage your profile and the contact details used for
                        neighbourhood activity.
                    </p>
                </header>

                <section className="border-b border-white/10 py-7">
                    <div className="mb-5 flex items-center gap-2">
                        <UserIcon className="size-4 text-emerald-400" />
                        <h2 className="text-base font-semibold text-white">
                            Profile
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                        <div>
                            <label
                                htmlFor="first-name"
                                className="text-sm font-medium text-white"
                            >
                                First name
                            </label>
                            <input
                                id="first-name"
                                type="text"
                                className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="last-name"
                                className="text-sm font-medium text-white"
                            >
                                Last name
                            </label>
                            <input
                                id="last-name"
                                type="text"
                                className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                            />
                        </div>
                    </div>
                </section>
            </div>
        </main>
    );
}
