"use client";

import {
    Users,
} from "lucide-react";

export default function PropertyMembers() {
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
										Manage the people who have access to this
										property.
								</p>
							</div>
						</div>
					</header>

					<section className="mt-7">
						<div className="rounded-xl border border-border bg-card p-6">
							<h2 className="text-lg font-semibold">
									Members
							</h2>

							<p className="mt-1 text-sm text-muted-foreground">
									Property members will appear here.
							</p>
						</div>
					</section>
				</div>
			</main>
    );
}
