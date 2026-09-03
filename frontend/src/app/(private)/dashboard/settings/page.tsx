"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bell, Loader2, Shield, User as UserIcon } from "lucide-react";
import { toast } from "sonner";
import { fetchUserSettings, updateUserSettings } from "@/lib/api/userSettings";
import { useQueryClient } from "@tanstack/react-query";
import { updateStoredFullName } from "@/lib/auth/cognito";

const PHONE_PATTERN = /^\+?[0-9\s\-()]{7,20}$/;

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [email, setEmail] = useState("");
    const [phoneNumber, setPhoneNumber] = useState("");
    const [systemRole, setSystemRole] = useState("");

    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);


    useEffect(() => {
        let cancelled = false;

        fetchUserSettings()
            .then((data) => {
                if (cancelled) return;

                setFirstName(data.first_name ?? "");
                setLastName(data.last_name ?? "");
                setEmail(data.email);
                setPhoneNumber(data.phone_number ?? "");
                setSystemRole(data.system_role);
            })
            .catch((error) => {
                if (cancelled) return;

                toast.error(
                    error instanceof Error
                        ? error.message
                        : "Failed to load settings.",
                );
            })
            .finally(() => {
                if (cancelled) return;
                setIsLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, []);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!firstName.trim() || !lastName.trim()) {
            toast.error("First and last name are required.");
            return;
        }

        const trimmedPhoneNumber = phoneNumber.trim();

        if (
            trimmedPhoneNumber &&
            !PHONE_PATTERN.test(trimmedPhoneNumber)
        ) {
            toast.error("Enter a valid phone number.");
            return;
        }

        setIsSaving(true);

        try {
            const data = await updateUserSettings({
                first_name: firstName.trim(),
                last_name: lastName.trim(),
                phone_number: trimmedPhoneNumber || null,
            });

            setFirstName(data.first_name ?? "");
            setLastName(data.last_name ?? "");
            setPhoneNumber(data.phone_number ?? "");

            const fullName = `${data.first_name} ?? "" ${data.last_name} ?? ""`.trim();
            updateStoredFullName(fullName);
            queryClient.invalidateQueries({ queryKey: ["userContext"]});
            toast.success("Settings updated");
        } catch (error) {
            toast.error(
                error instanceof Error
                    ? error.message
                    : "Failed to update settings.",
            );
        } finally {
            setIsSaving(false);
        }
    };


    if (isLoading) {
        return (
            <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
                <div className="flex min-h-64 items-center justify-center">
                    <Loader2 className="size-5 animate-spin text-brand-green" />
                </div>
            </main>
        );
    }



    return (
        <main className="min-h-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="max-w-full">
                <header className="border-b border-border pb-7">
                    <p className="text-sm text-brand-green">Settings</p>
                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                        Account settings
                    </h1>
                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-brand-ash">
                        Manage your profile and the contact details used for
                        neighbourhood activity.
                    </p>
                </header>

                <form onSubmit={handleSubmit}>
                    <section className="border-b border-border py-7">
                        <div className="mb-5 flex items-center gap-2">
                            <UserIcon className="size-4 text-brand-green" />
                            <h2 className="text-base font-semibold text-brand-frost">
                                Profile
                            </h2>
                        </div>
                        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                            <div>
                                <label
                                    htmlFor="first-name"
                                    className="text-sm font-medium text-brand-frost"
                                >
                                    First name
                                </label>
                                <input
                                    id="first-name"
                                    type="text"
                                    value={firstName}
                                    onChange={(event) => setFirstName(event.target.value)}
                                    className="mt-2 h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
                                />
                            </div>
                            <div>
                                <label
                                    htmlFor="last-name"
                                    className="text-sm font-medium text-brand-frost"
                                >
                                    Last name
                                </label>
                                <input
                                    id="last-name"
                                    type="text"
                                    value={lastName}
                                    onChange={(event) => setLastName(event.target.value)}
                                    className="mt-2 h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
                                />
                            </div>
                        </div>
                    </section>
                    <section className="border-b border-border py-7">
                        <div className="mb-5 flex items-center gap-2">
                            <Bell className="size-4 text-brand-green" />
                            <h2 className="text-base font-semibold text-brand-frost">
                                Notifications
                            </h2>
                        </div>
                        <div className="space-y-5">
                            <div>
                                <label
                                    htmlFor="email"
                                    className="text-sm font-medium text-brand-frost"
                                >
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    readOnly
                                    className="mt-2 h-10 w-full cursor-not-allowed rounded-md border border-border bg-brand-abyss/50 px-3 text-sm text-brand-ash outline-none"
                                />
                                <p className="mt-2 text-xs text-brand-ash/70">
                                    This email is managed through your account
                                    authentication.
                                </p>
                            </div>
                            <div>
                                <label
                                    htmlFor="phone"
                                    className="text-sm font-medium text-brand-frost"
                                >
                                    Phone number
                                </label>
                                <input
                                    id="phone"
                                    type="tel"
                                    value={phoneNumber}
                                    onChange={(event) => setPhoneNumber(event.target.value)}
                                    placeholder="+27 82 000 0000"
                                    className="mt-2 h-10 w-full rounded-md border border-border bg-brand-abyss px-3 text-sm text-brand-frost outline-none placeholder:text-brand-ash/60 focus:border-brand-green/60"
                                />
                                <p className="mt-2 text-xs text-brand-ash/70">
                                    Used for WhatsApp alerts.
                                </p>
                            </div>
                        </div>
                    </section>
                    <section className="border-b border-border py-7">
                        <div className="mb-5 flex items-center gap-2">
                            <Shield className="size-4 text-brand-green" />
                            <h2 className="text-base font-semibold text-brand-frost">
                                Account
                            </h2>
                        </div>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <div className="rounded-md border border-border bg-brand-abyss px-4 py-3">
                                <p className="text-xs text-brand-ash/70">
                                    System role
                                </p>
                                <p className="mt-1 text-sm font-medium text-brand-frost">
                                    {systemRole}
                                </p>
                            </div>
                        </div>
                    </section>
                    <section className="pt-6">
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-brand-green px-3.5 text-sm font-medium text-brand-void transition-colors hover:bg-brand-green"
                            >
                                {isSaving && (
                                    <Loader2 className="size-4 animate-spin" />
                                )}
                                {isSaving ? "Saving..." : "Save changes"}
                            </button>
                        </div>
                    </section>
                </form>

            </div>
        </main>
    );
}
