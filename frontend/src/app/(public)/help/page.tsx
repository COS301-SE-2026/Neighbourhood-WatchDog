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
    },
    {
        title: "Property administrators",
        description: "Manage property members and cameras.",
        href: "#property-admin",
        icon: Camera
    },
    {
        title: "Neighbourhood administrators",
        description: "Manage membership and neighbourhood activity.",
        href: "#neighbourhood-admin",
        icon: ShieldCheck
    },
    {
        title: "Security officers",
        description: "Respond to critical dispatches.",
        href: "#security-officer",
        icon: BellRing
    },
    {
        title: "Notifications",
        description: "Set up and troubleshoot alerts.",
        href: "#notifications",
        icon: BellRing
    },
    {
        title: "Privacy",
        description: "Understand camera and footage access.",
        href: "#privacy",
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
            "Check the detection type, severity, camera, confidence, and time. Open Details for available evidence and follow your role’s response procedure. Only accept or close an alert when you are authorised to do so."
    },

    {
        question: "Does acknowledging an alert resolve the incident?",
        answer:
            "No. Accepting an officer dispatch acknowledges the alert and indicates that a responder is handling it. The incident remains active until an authorised responder resolves or dismisses it."
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

    return (
        <main className="dark min-h-full w-full bg-brand-void px-6 py-7 text-brand-frost md:px-8">
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
                            <li><strong className="text-brand-frost">1. Create and confirm your account.</strong> Use your email address, enter the confirmation code, and complete MFA when prompted.</li>
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
                                "Select Add camera and enter the camera details supplied by the deployment operator.",
                                "Choose Private, Neighbourhood, or Public visibility for the intended audience.",
                                "Configure detection zones for areas the camera should monitor.",
                                "Open Members to invite people who need access to the property.",
                                "Check whether the camera is Live, Connecting, Unavailable, or Disabled, then open its live view when available."
                            ]}

                        />
                        <TutorialCard
                            id="alert-tutorial"
                            icon={BellRing}
                            title="Respond to an alert"
                            summary="Review the evidence and communicate responsibly."
                            steps={[
                                "Open Live alerts or Critical alerts and check the detection type, severity, camera, confidence, and time.",
                                "Select Details to review the available thumbnail, clip, and alert information.",
                                "Follow your neighbourhood’s response procedure for weapon or fall detections.",
                                "Accepting an officer dispatch acknowledges that alert; authorised responders can later resolve or dismiss it.",
                                "Use Broadcast only for an active alert appropriate for neighbourhood-wide communication."
                            ]}

                        />
                        <TutorialCard
                            id="agent-tutorial"
                            icon={KeyRound}
                            title="Pair the WatchDog Agent"
                            summary="Connect the trusted local Agent to the selected property."
                            steps={[
                                "Download the Windows WatchDog Agent from the Downloads section on the landing page.",
                                "Open Connect agent and confirm the correct property.",
                                "Generate a pairing token and enter it in the trusted Agent setup application before it expires.",
                                "Confirm that the Agent is paired and the required camera is enabled.",
                                "If the Agent is offline or the stream is unavailable, check its connection, camera configuration, and network before trying again.",
                                "Never include pairing tokens or camera connection details in screenshots or reports."
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
                        <TutorialCard
                            id="property-admin"
                            icon={Camera}
                            title="Property administrators"
                            summary="Manage the people and cameras connected to your property."
                            steps={[
                                "Select the correct property in the dashboard.",
                                "Open Members to invite or remove property members.",
                                "Open My cameras to register a camera and choose its visibility.",
                                "Configure detection zones and review camera status.",
                                "Use Connect agent to generate a pairing token for the trusted operator."
                            ]}
                        />
                        <TutorialCard
                            id="neighbourhood-admin"
                            icon={ShieldCheck}
                            title="Neighbourhood administrators"
                            summary="Manage membership and review neighbourhood activity."
                            steps={[
                                "Share the neighbourhood join code through an approved channel.",
                                "Review join requests before approving membership.",
                                "Use Critical alerts and the Map to review active incidents.",
                                "Use Dispatches and Analytics to review response activity and trends."
                            ]}
                        />
                        <TutorialCard
                            id="security-officer"
                            icon={BellRing}
                            title="Security officers"
                            summary="Respond to critical alerts assigned to you."
                            steps={[
                                "Go on duty and allow location access before responding.",
                                "Review a dispatch request and accept or decline it.",
                                "After accepting, review the selected alert and route on the security map.",
                                "Review available footage, tracking history, and the situational brief.",
                                "Resolve or dismiss the alert when your response is complete."
                            ]}
                        />
                        <TutorialCard
                            id="notifications"
                            icon={BellRing}
                            title="Notifications"
                            summary="Understand how to receive and verify alerts."
                            steps={[
                                "Allow device notifications if you want push alerts.",
                                "Keep your account contact details up to date.",
                                "If notifications stop, check device permissions and connectivity.",
                                "Open the dashboard to verify an alert’s current state before acting."
                            ]}
                        />
                        <TutorialCard
                            id="privacy"
                            icon={KeyRound}
                            title="Camera and footage privacy"
                            summary="Understand visibility and handle evidence carefully."
                            steps={[
                                "Choose Private, Neighbourhood, or Public visibility for the intended audience.",
                                "Only authorised users should access restricted cameras and footage.",
                                "Never publish clips, home addresses, pairing tokens, or camera credentials.",
                                "Report unexpected access to your administrator."
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
                            href="/"
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