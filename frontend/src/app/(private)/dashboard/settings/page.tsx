"use client";

import { Bell, Shield, User as UserIcon } from "lucide-react";

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


                <section className="border-b border-white/10 py-7">
                    <div className="mb-5 flex items-center gap-2">
                        <Bell className="size-4 text-emerald-400" />
                        <h2 className="text-base font-semibold text-white">
                            Notifications
                        </h2>
                    </div>

                    <div className="space-y-5">
                        <div>
                            <label
                                htmlFor="email"
                                className="text-sm font-medium text-white"
                            >
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                readOnly
                                className="mt-2 h-10 w-full cursor-not-allowed rounded-md border border-white/10 bg-zinc-950/50 px-3 text-sm text-white/50 outline-none"
                            />
                            <p className="mt-2 text-xs text-white/40">
                                This email is managed through your account
                                authentication.
                            </p>
                        </div>

                        <div>
                            <label
                                htmlFor="phone"
                                className="text-sm font-medium text-white"
                            >
                                Phone number
                            </label>
                            <input
                                id="phone"
                                type="tel"
                                placeholder="+27 82 000 0000"
                                className="mt-2 h-10 w-full rounded-md border border-white/10 bg-zinc-950 px-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-emerald-500/60"
                            />
                            <p className="mt-2 text-xs text-white/40">
                                Used for WhatsApp alerts.
                            </p>
                        </div>
                    </div>
                </section>

                <section className="border-b border-white/10 py-7">
                    <div className="mb-5 flex items-center gap-2">
                        <Shield className="size-4 text-emerald-400" />
                        <h2 className="text-base font-semibold text-white">
                            Account
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div className="rounded-md border border-white/10 bg-zinc-950 px-4 py-3">
                            <p className="text-xs text-white/40">
                                System role
                            </p>
                            <p className="mt-1 text-sm font-medium text-white">
                                -
                            </p>
                        </div>
                    </div>
                </section>


            </div>
        </main>
    );
}
