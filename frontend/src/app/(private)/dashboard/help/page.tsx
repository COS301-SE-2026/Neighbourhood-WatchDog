"use client";

import { usePropertyContext } from "@/hooks/use-property-context";
import Link from "next/link";
import {
    ArrowRight,
    BellRing,
    BookOpen,
    Camera,
    CircleHelp,
    ExternalLink,
    KeyRound,
    LifeBuoy,
    ShieldCheck,
    type LucideIcon
} from "lucide-react";


const quickLinks = [

    {
        title: "Getting started",
        description: "Create an account, register a property, and join a neighbourhood.",
        href: "#getting-started",
        icon: BookOpen
    },
    {
        title: "Camera tutorial",
        description: "Add a camera, understand its status, and configure monitoring.",
        href: "#camera-tutorial",
        icon: Camera
    },
    {
        title: "Alert tutorial",
        description: "Review, acknowledge, and safely broadcast an alert.",
        href: "#alert-tutorial",
        icon: BellRing
    },
    {
        title: "Agent pairing",
        description: "Connect the trusted WatchDog Agent to a property.",
        href: "#agent-tutorial",
        icon: KeyRound
    }
];



const faqs = [
    {
        question: "Why can I not see a Help or administration option?",
        answer:
            "Dashboard options depend on your selected property, neighbourhood membership, and account role. Check the property selector first. If the option is still missing, ask a neighbourhood or system administrator to confirm your permissions."
    },
    {
        question: "What does a camera status mean?",
        answer:
            "Live means the stream is available. Connecting means WatchDog is trying to start it. Unavailable means the stream cannot currently be played. Disabled means monitoring has been turned off for that camera."
    },
    {
        question: "What should I do when I receive an alert?",
        answer:
            "Read the severity, detection type, camera, confidence, and time. Open Details when you need more information, follow the neighbourhood response procedure, and acknowledge the alert only when a responsible person is handling it."
    },
    {
        question: "Does acknowledging an alert resolve the incident?",
        answer:
            "No. Acknowledging tells other responders that someone has seen and is handling the alert. Continue following the applicable safety procedure until the incident is resolved."
    },
    {
        question: "Why is a camera clip or thumbnail unavailable?",
        answer:
            "Supporting footage may still be processing, may not have been captured, or may be unavailable for that event. Use the available alert information and follow the response procedure instead of repeatedly submitting the same action."
    },
    {
        question: "How do I keep pairing tokens and camera details safe?",
        answer:
            "Treat pairing tokens, camera connection details, passwords, and account information as sensitive. Share them only with the authorised deployment operator and never include them in screenshots, reports, or public messages."
    }
];

function SectionHeading({eyebrow, title, description}: {

    readonly eyebrow: string;
    readonly title: string;
    readonly description: string;
}) {
    return (
        <div className="mb-5">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-brand-green">
                {eyebrow}
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-brand-frost">
                {title}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-brand-ash">
                {description}
            </p>
        </div>
    );
}

function TutorialCard({id, icon: Icon, title, summary, steps}: {
    readonly id: string;
    readonly icon: LucideIcon;
    readonly title: string;
    readonly summary: string;
    readonly steps: string[];

}) {
    return (
        <article
            id={id}
            className="scroll-mt-8 rounded-xl border border-border bg-brand-abyss p-5"
        >
            <div className="flex items-start gap-3">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-green/10">
                    <Icon className="size-4 text-brand-green" />
                </div>
                <div>
                    <h3 className="text-base font-semibold text-brand-frost">{title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-brand-ash">{summary}</p>
                </div>
            </div>
            <ol className="mt-5 space-y-3 border-l border-border pl-5 text-sm text-brand-ash">
                {steps.map((step, index) => (
                    <li key={step} className="relative leading-relaxed">
                        <span className="absolute -left-[2rem] flex size-5 items-center justify-center rounded-full border border-brand-green/40 bg-brand-abyss text-[10px] font-semibold text-brand-green">
                            {index + 1}
                        </span>
                        {step}
                    </li>
                ))}
            </ol>
        </article>
    );

    
}

export default function HelpPage() {
    const { activeContext } = usePropertyContext();

    const dashboardHref = activeContext ? `/dashboard/properties/${activeContext.propertyId}/cameras` : "/dashboard";

    return (
        <main className="min-h-full w-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
            <div className="mx-auto max-w-5xl">
                <header className="border-b border-border pb-7">
                    <div className="flex items-start gap-4">
                        <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-brand-green/10">
                            <CircleHelp className="size-6 text-brand-green" />
                        </div>
                        <div>
                            <p className="text-sm text-brand-green">WatchDog support</p>
                            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
                                Help centre
                            </h1>
                            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-brand-ash">
                                Learn how to set up your property, monitor cameras, and respond to alerts. Select a topic below or browse the frequently asked questions.
                            </p>
                        </div>
                    </div>
                </header>

                <nav
                    aria-label="Help centre sections"
                    className="grid gap-3 border-b border-border py-7 sm:grid-cols-2 xl:grid-cols-4"
                >
                    {quickLinks.map(({ title, description, href, icon: Icon }) => (
                        <a
                            key={href}
                            href={href}
                            className="group rounded-xl border border-border bg-brand-depth p-4 transition-colors hover:border-brand-green/40 hover:bg-brand-green/10"
                        >
                            <Icon className="size-4 text-brand-green" />
                            <p className="mt-3 text-sm font-semibold text-brand-frost">{title}</p>
                            <p className="mt-1 text-xs leading-relaxed text-brand-ash">
                                {description}
                            </p>
                            <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-brand-green">
                                Read guide
                                <ArrowRight className="size-3 transition-transform group-hover:translate-x-0.5" />
                            </span>
                        </a>
                    ))}
                </nav>

                <section id="getting-started" className="scroll-mt-8 border-b border-border py-8">
                    <SectionHeading
                        eyebrow="Start here"
                        title="Getting started"
                        description="Complete these steps in order before expecting camera detections and neighbourhood alerts."
                    />
                    <div className="rounded-xl border border-border bg-brand-abyss p-5">
                        <ol className="space-y-4 text-sm text-brand-ash">
                            <li><strong className="text-brand-frost">1. Create and confirm your account.</strong> Use your email address and enter the confirmation code sent to you.</li>
                            <li><strong className="text-brand-frost">2. Create a property.</strong> Search for and select the correct property address.</li>
                            <li><strong className="text-brand-frost">3. Create or join a neighbourhood.</strong> Administrators create a neighbourhood; residents submit a join request with the administrator&apos;s join code.</li>
                            <li><strong className="text-brand-frost">4. Add cameras.</strong> Register the camera name, physical location, and connection information supplied by the deployment operator.</li>
                            <li><strong className="text-brand-frost">5. Connect the Agent.</strong> Generate a one-time pairing token and provide it only to the authorised Agent operator.</li>
                        </ol>
                    </div>
                </section>

                <section id="tutorials" className="scroll-mt-8 border-b border-border py-8">
                    <SectionHeading
                        eyebrow="Step-by-step tutorials"
                        title="Use WatchDog confidently"
                        description="These short guides explain the actions users perform most often."
                    />
                    <div className="grid gap-4 lg:grid-cols-2">
                        <TutorialCard
                            id="camera-tutorial"
                            icon={Camera}
                            title="Manage cameras"
                            summary="Add a camera, understand its status, and open its live view."
                            steps={[
                                "Open My cameras for the correct property.",
                                "Select Add camera and complete the camera name, location, and connection fields.",
                                "Read the status on the camera card: Live, Connecting, Unavailable, or Disabled.",
                                "Select an enabled camera to open the live view; close the view when finished." 

                            ]}
                        />
                        <TutorialCard
                            id="alert-tutorial"
                            icon={BellRing}
                            title="Respond to an alert"
                            summary="Review the evidence and communicate responsibly."
                            steps={[
                                "Open Live alerts and check the severity, detection type, camera, confidence, and time.",
                                "Select Details when you need the thumbnail, clip, or full alert information.",
                                "Follow the neighbourhood response procedure.",
                                "Select Acknowledge only when a responsible person is handling the alert.",
                                "Use Broadcast only for an active alert that is appropriate for neighbourhood-wide communication."


                            ]}
                        />
                        <TutorialCard
                            id="agent-tutorial"
                            icon={KeyRound}
                            title="Pair the WatchDog Agent"
                            summary="Connect the trusted local Agent to the selected property."
                            steps={[
                                "Open Connect agent and confirm the property address.",
                                "Select Generate pairing token, then Copy token.",
                                "Enter the token in the trusted Agent setup application before it expires.",
                                "Confirm that the Agent is paired, then enable the required camera.",
                                "Never include the token or camera connection details in screenshots or reports."
                            ]}
                        />
                        <TutorialCard
                            id="settings-tutorial"
                            icon={ShieldCheck}
                            title="Update account settings"
                            summary="Maintain the profile and contact information used by the deployment."
                            steps={[
                                "Open Settings from the Account section.",
                                "Update your first name, last name, or phone number.",
                                "Remember that the authentication email is read-only on this screen.",
                                "Select Save changes and wait for the confirmation message." 
                            ]}
                        />
                    </div>
                </section>

                <section id="faqs" className="scroll-mt-8 border-b border-border py-8">
                    <SectionHeading
                        eyebrow="Frequently asked questions"
                        title="Find a quick answer"
                        description="Select a question to expand its answer."
                    />
                    <div className="space-y-3">
                        {faqs.map(({ question, answer }) => (
                            <details key={question} className="group rounded-xl border border-border bg-brand-abyss">
                                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 text-sm font-medium text-brand-frost [&::-webkit-details-marker]:hidden">
                                    {question}
                                    <span className="text-xl font-light text-brand-green transition-transform group-open:rotate-45">+</span>
                                </summary>
                                <p className="border-t border-border px-5 py-4 text-sm leading-relaxed text-brand-ash">
                                    {answer}
                                </p>
                            </details>
                        ))}
                    </div>
                </section>

                <section id="contact-support" className="scroll-mt-8 py-8">
                    <div className="flex flex-col gap-4 rounded-xl border border-brand-green/20 bg-brand-green/10 p-5 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex items-start gap-3">
                            <LifeBuoy className="mt-0.5 size-5 shrink-0 text-brand-green" />
                            <div>
                                <h2 className="text-base font-semibold text-brand-frost">Still need help?</h2>
                                <p className="mt-1 text-sm leading-relaxed text-brand-ash">
                                    Record the page name, visible error message, approximate time, and a redacted screenshot. Contact the WatchDog deployment administrator through the approved project support channel.
                                </p>
                            </div>
                        </div>
                        <Link
                            href={dashboardHref}
                            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md border border-brand-gunmetal/20 px-3.5 py-2 text-sm font-medium text-brand-ash transition-colors hover:bg-brand-slate hover:text-brand-frost"
                        >
                            Back to dashboard
                            <ExternalLink className="size-3.5" />
                        </Link>
                    </div>
                </section>
            </div>
        </main>
    );
}