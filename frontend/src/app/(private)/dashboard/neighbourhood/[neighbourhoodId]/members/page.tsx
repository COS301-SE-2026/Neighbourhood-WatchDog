"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Loader2, Users } from "lucide-react";
import { useParams } from "next/navigation";

import { useUserContext } from "@/hooks/use-user-context";
import { getNeighbourhoodMembers, updateNeighbourhoodMemberRole } from "@/lib/api/neighbourhood";
import type { NeighbourhoodMemberRes } from "@/lib/validators/neighbourhood";


const MEMBER_ROLES: NeighbourhoodMemberRes["role"][] = [
    "RESIDENT",
    "SECURITY_OFFICER",
    "NEIGHBOURHOOD_ADMIN"
];

function formatRole(role: NeighbourhoodMemberRes["role"]) {
    return role
        .toLowerCase()
        .replaceAll("_", " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function MembersPage() {
    const { neighbourhoodId } = useParams<{neighbourhoodId: string}>();

    const {
        data: userContext,
        isLoading: userContextLoading,
    } = useUserContext();

    const isNeighbourhoodAdmin = Boolean(
        userContext?.properties.some(
            (property) =>
                property.neighbourhood?.id === neighbourhoodId &&
                property.neighbourhood?.role === "NEIGHBOURHOOD_ADMIN",
        ),
    );

    const [members, setMembers] = useState<NeighbourhoodMemberRes[]>([]);
    const [membersLoading, setMembersLoading] = useState(true);
    const [membersError, setMembersError] = useState<string | null>(null);

    const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);
    const [roleError, setRoleError] = useState<string | null>(null);


    const handleRoleChange = async (
        memberUserId: string,
        role: NeighbourhoodMemberRes["role"],
    ) => {
        setRoleError(null);
        setUpdatingMemberId(memberUserId);

        try {
            const updatedMember = await updateNeighbourhoodMemberRole(
                neighbourhoodId,
                memberUserId,
                { role },
            );

            setMembers((currentMembers) =>
                currentMembers.map((member) =>
                    member.user_id === updatedMember.user_id
                        ? updatedMember
                        : member,
                ),
            );
        } catch (error: unknown) {
            setRoleError(
                error instanceof Error
                    ? error.message
                    : "Failed to update member role.",
            );
        } finally {
            setUpdatingMemberId(null);
        }
    };


    useEffect(() => {
        if (userContextLoading || !isNeighbourhoodAdmin) {
            return;
        }

        let cancelled = false;

        getNeighbourhoodMembers(neighbourhoodId)
            .then((data) => {
                if (cancelled) return;

                setMembers(data);
                setMembersError(null);
            })
            .catch((error: unknown) => {
                if (cancelled) return;

                setMembersError(
                    error instanceof Error
                        ? error.message
                        : "Failed to load neighbourhood members.",
                );
            })
            .finally(() => {
                if (!cancelled) {
                    setMembersLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [
        neighbourhoodId,
        userContextLoading,
        isNeighbourhoodAdmin,
    ]);

    if (userContextLoading) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto flex max-w-5xl items-center justify-center py-20">
                    <Loader2 className="size-5 animate-spin text-emerald-400" />
                </div>
            </main>
        );
    }

    if (!isNeighbourhoodAdmin) {
        return (
            <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
                <div className="mx-auto max-w-5xl">
                    <p className="text-sm text-white/60">
                        You don&apos;t have admin access to this neighbourhood.
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-full bg-black px-6 py-7 text-white md:px-8">
            <div className="mx-auto max-w-5xl">
                <header className="border-b border-white/10 pb-7">
                    <p className="text-sm text-emerald-400">
                        Neighbourhood management
                    </p>

                    <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                        Members
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/50">
                        View members of this neighbourhood and manage their
                        roles.
                    </p>
                </header>

                <section className="pt-7">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Users className="size-4 text-emerald-400" />

                        <div>
                            <h2 className="text-sm font-medium text-white">
                                Neighbourhood members
                            </h2>

                            <p className="mt-1 text-sm text-white/40">
                                {members.length} member
                                {members.length === 1 ? "" : "s"}
                            </p>
                        </div>
                    </div>

                    {roleError && (
                        <div
                            role="alert"
                            className="mt-4 flex items-start gap-3 border border-red-500/25 bg-red-500/[0.08] px-4 py-3 text-sm text-red-200"
                        >
                            <AlertCircle className="mt-0.5 size-4 shrink-0 text-red-400" />

                            <p>{roleError}</p>
                        </div>
                    )}


                    {membersLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="size-5 animate-spin text-emerald-400" />
                        </div>
                    ) : membersError ? (
                        <div
                            role="alert"
                            className="mt-4 flex items-start gap-3 border border-red-500/25 bg-red-500/[0.08] px-4 py-3 text-sm text-red-200"
                        >
                            <AlertCircle className="mt-0.5 size-4 shrink-0 text-red-400" />
                            <p>{membersError}</p>
                        </div>
                    ) : members.length === 0 ? (
                        <div className="border-b border-white/10 py-16 text-center">
                            <p className="text-sm font-medium text-white/65">
                                No members found
                            </p>

                            <p className="mt-2 text-sm text-white/40">
                                Members will appear here once they join the
                                neighbourhood.
                            </p>
                        </div>
                    ) : (
                        <div className="divide-y divide-white/10">
                            {members.map((member) => (
                                <div
                                    key={member.user_id}
                                    className="flex items-center justify-between gap-4 py-4"
                                >
                                    <div className="min-w-0">
                                        <p className="truncate text-sm font-medium text-white">
                                            {member.first_name} {member.last_name}
                                        </p>

                                        <p className="mt-1 truncate text-sm text-white/45">
                                            {member.email}
                                        </p>
                                    </div>

                                    <div className="flex shrink-0 items-center gap-2">
                                        {updatingMemberId === member.user_id && (
                                            <Loader2 className="size-4 animate-spin text-emerald-400" />
                                        )}

                                        <select
                                            value={member.role}
                                            onChange={(event) =>
                                                handleRoleChange(
                                                    member.user_id,
                                                    event.target.value as NeighbourhoodMemberRes["role"],
                                                )
                                            }
                                            disabled={updatingMemberId === member.user_id}
                                            aria-label={`Role for ${member.first_name} ${member.last_name}`}
                                            className="h-9 rounded-md border border-white/10 bg-white/[0.04] px-3 text-xs text-white outline-none transition-colors focus:border-emerald-400/60 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            {MEMBER_ROLES.map((role) => (
                                                <option
                                                    key={role}
                                                    value={role}
                                                    className="bg-zinc-950 text-white"
                                                >
                                                    {formatRole(role)}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </main>
    );
}
