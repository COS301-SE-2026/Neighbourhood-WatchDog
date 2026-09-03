"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
	AlertTriangle,
  Loader2,
  Mail,
	MailPlus,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from "@/components/ui/alert-dialog";

import { useUserContext } from "@/hooks/use-user-context";
import { getPropertyMembers, invitePropertyMember, removePropertyMember } from "@/lib/api/property";
import type { PropertyMembers, PropertyMember } from "@/lib/validators/property";

export default function PropertyMembers() {
  const { propertyId } = useParams<{propertyId: string}>();

	const { data: userContext } = useUserContext();

	const isPropertyAdmin = Boolean(
		userContext?.properties.some(
			(property) =>
				property.id === propertyId &&
				property.is_admin
		),
	);

  const [members, setMembers] = useState<PropertyMembers["members"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
	const [removingUserId, setRemovingUserId] = useState<string | null>(null);
	const [actionError, setActionError] = useState<string | null>(null);
	const [memberToRemove, setMemberToRemove] = useState<PropertyMember | null>(null);

	const [inviteEmail, setInviteEmail] = useState("");

	const [inviteLoading, setInviteLoading] = useState(false);
	const [inviteError, setInviteError] = useState<string | null>(null);
	const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getPropertyMembers(propertyId)
      .then((result) => {
        if (cancelled) {
          return;
        }

        setMembers(result.members);
      })
      .catch((requestError: unknown) => {
        if (cancelled) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load property members.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [propertyId]);

	async function handleInviteSubmit(
		event: React.FormEvent<HTMLFormElement>,
	) {

		
		event.preventDefault();

		if (!isPropertyAdmin) {
			return;
		}

		const email = inviteEmail.trim().toLowerCase();

		if (!email) {
			return;
		}

		setInviteLoading(true);
		setInviteError(null);
		setInviteSuccess(null);

		try {
			await invitePropertyMember(propertyId, {
				email,
			});

			const result = await getPropertyMembers(propertyId);

			setMembers(result.members);
			setInviteEmail("");
			setInviteSuccess(
				`Invitation sent to ${email}.`,
			);
		} catch (requestError: unknown) {
			setInviteError(
				requestError instanceof Error
					? requestError.message
					: "Failed to invite property member.",
			);
		} finally {
			setInviteLoading(false);
		}
	}

	async function handleRemoveMember() {
		if (
			!memberToRemove ||
			!isPropertyAdmin ||
			memberToRemove.is_admin
		) {
			return;
		}

		const member = memberToRemove;

		setRemovingUserId(member.user_id);
		setActionError(null);

		try {
			await removePropertyMember(
				propertyId,
				member.user_id,
			);

			setMembers((currentMembers) =>
				currentMembers.filter(
					(currentMember) =>
						currentMember.user_id !== member.user_id,
				),
			);

			setMemberToRemove(null);
		} catch (requestError: unknown) {
			setActionError(
				requestError instanceof Error
					? requestError.message
					: "Failed to remove property member.",
			);
		} finally {
			setRemovingUserId(null);
		}
	}




  return (
    <main className="min-h-full bg-background px-6 py-8 text-foreground md:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="border-b border-border pb-6">
          <p className="text-sm text-primary">
            My home
          </p>

          <div className="mt-2 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg border border-primary/25 bg-primary/10">
              <Users className="size-5 text-primary" />
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Property members
              </h1>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Manage the people who have access to this property.
              </p>
            </div>
          </div>
        </header>

				{isPropertyAdmin && (
						<section className="mt-7">
							<div className="rounded-xl border border-border bg-card p-6">
								<div className="flex items-start gap-3">
									<div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-primary/25 bg-primary/10">
										<MailPlus className="size-4 text-primary" />
									</div>

									<div>
										<h2 className="text-lg font-semibold">
											Add a member
										</h2>

										<p className="mt-1 text-sm text-muted-foreground">
											Add an existing WatchDog user to access this property.
										</p>
									</div>
								</div>

								<form
									onSubmit={handleInviteSubmit}
									className="mt-5 flex flex-col gap-3 sm:flex-row"
								>
									<div className="relative flex-1">
										<Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

										<input
											type="email"
											value={inviteEmail}
											onChange={(event) => setInviteEmail(event.target.value)}
											placeholder="Enter their email address"
											aria-label="Invitee email address"
											className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
										/>
									</div>

									<button
										type="submit"
										disabled={inviteLoading || !inviteEmail.trim()}
										className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
									>
										{inviteLoading ? (
												<>
													<Loader2 className="mr-2 size-4 animate-spin" />
													Sending...
												</>
											) : (
												"Send invitation"
											)}
									</button>
								</form>

								{inviteSuccess && (
									<p className="mt-3 text-sm text-primary">
										{inviteSuccess}
									</p>
								)}

								{inviteError && (
									<p
										role="alert"
										className="mt-3 text-sm text-destructive"
									>
										{inviteError}
									</p>
								)}

							</div>
						</section>
					)
				}
			
				{actionError && (
					<div
						role="alert"
						className="mt-6 rounded-xl border border-destructive/30 bg-destructive/10 px-5 py-4 text-sm text-destructive"
					>
						{actionError}
					</div>
				)}

        <section className="mt-7">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">
                Members
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Users currently connected to this property.
              </p>
            </div>

            {!loading && !error && (
              <span className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
                {members.length}{" "}
                {members.length === 1
                  ? "member"
                  : "members"}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center rounded-xl border border-border bg-card py-20">
              <Loader2 className="size-5 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div
              role="alert"
              className="rounded-xl border border-destructive/30 bg-destructive/10 px-5 py-4 text-sm text-destructive"
            >
              {error}
            </div>
          ) : members.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card px-6 py-16 text-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                <UserRound className="size-5 text-muted-foreground" />
              </div>

              <h3 className="mt-4 text-sm font-semibold">
                No members yet
              </h3>

              <p className="mt-1 text-sm text-muted-foreground">
                Property members will appear here.
              </p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="divide-y divide-border">
                {members.map((member) => {
                  const fullName = [
                    member.first_name,
                    member.last_name,
                  ]
                    .filter(Boolean)
                    .join(" ");

                  return (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-muted/40"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-primary/25 bg-primary/10">
                          <UserRound className="size-4 text-primary" />
                        </div>

                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {fullName || member.email}
                          </p>

                          <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-muted-foreground">
                            <Mail className="size-3" />
                            {member.email}
                          </p>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-2">
												{member.is_admin && (
													<span className="inline-flex items-center gap-1 rounded-full border border-primary/25 bg-primary/10 px-2.5 py-1 text-xs text-primary">
														<ShieldCheck className="size-3.5" />
														Admin
													</span>
												)}

												{isPropertyAdmin && !member.is_admin && (
													<button
														type="button"
														onClick={() => setMemberToRemove(member)}
														disabled={removingUserId !== null}
														className="rounded-md border border-destructive/30 px-2.5 py-1 text-xs text-destructive transition-colors hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-50"
													>
														Remove
													</button>
												)}

											</div>

                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      </div>


			<AlertDialog
				open={memberToRemove !== null}
				onOpenChange={(open) => {
					if (!open && removingUserId === null) {
						setMemberToRemove(null);
					}
				}}
			>
				<AlertDialogContent className="border-border bg-card text-foreground">
					<AlertDialogHeader>
						<div className="mb-2 flex size-10 items-center justify-center rounded-lg border border-destructive/30 bg-destructive/10">
							<AlertTriangle className="size-5 text-destructive" />
						</div>

						<AlertDialogTitle>
							Remove property member?
						</AlertDialogTitle>

						<AlertDialogDescription className="text-muted-foreground">
							This will remove{" "}
							<span className="font-medium text-foreground">
								{memberToRemove
									? [
											memberToRemove.first_name,
											memberToRemove.last_name,
										]
											.filter(Boolean)
											.join(" ") || memberToRemove.email
									: ""}
							</span>{" "}
							from this property. They will lose access to the
							property cameras and alerts.
						</AlertDialogDescription>
					</AlertDialogHeader>

					<AlertDialogFooter>
						<AlertDialogCancel
							disabled={removingUserId !== null}
							className="border-border bg-transparent hover:bg-muted"
						>
							Cancel
						</AlertDialogCancel>

						<AlertDialogAction
							onClick={(event) => {
								event.preventDefault();
								void handleRemoveMember();
							}}
							disabled={removingUserId !== null}
							className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
						>
							{removingUserId !== null
								? "Removing..."
								: "Remove member"}
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>

    </main>
  );
}
