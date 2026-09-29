import Tag from "@/components/Tag";

const downloads = [
    {
        title: "Android application",
        description:
            "Stay connected to your neighbourhood, receive alerts, and monitor security activity from your Android device.",
        href:
            "https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/app-v0/watchdog.apk",
        buttonText: "Download Android APK",
    },
    {
        title: "Desktop application",
        description:
            "Run the WatchDog AI agent locally, connect cameras, and process detection events from your Windows computer.",
        href:
            "https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/Edge-Agent_v0.1.1/WatchDogSetup-0.1.1.exe",
        buttonText: "Download for Windows",
    },
];

export default function Downloads() {
    return (
        <section
            id="downloads"
            className="px-5 py-24 sm:px-8 lg:px-24"
        >
            <div className="container mx-auto">
                <div className="mx-auto max-w-2xl text-center">
                    <div className="flex justify-center">
                        <Tag>Downloads</Tag>
                    </div>

                    <h2 className="mt-6 text-5xl font-medium">
                        WatchDog wherever you{" "}
                        <span className="text-brand-green">
                            need protection
                        </span>
                    </h2>

                    <p className="mt-5 text-lg text-brand-ash">
                        Download the WatchDog mobile application or install
                        the desktop AI agent for your property.
                    </p>
                </div>

                <div className="mx-auto mt-12 grid max-w-5xl gap-6 lg:grid-cols-2">
                    {downloads.map((download) => (
                        <article
                            key={download.title}
                            className="flex flex-col rounded-3xl border border-border bg-brand-depth p-6"
                        >
                            <h3 className="mt-0 text-2xl font-medium">
                                {download.title}
                            </h3>

                            <p className="mt-3 text-brand-ash">
                                {download.description}
                            </p>

                            <a
                                href={download.href}
                                className="mt-5 inline-flex items-center justify-center rounded-xl bg-brand-green px-5 py-3 font-medium text-brand-void transition-colors hover:bg-brand-green/85 focus-visible:outline-brand-green"
                            >
                                {download.buttonText}
                            </a>
                        </article>
                    ))}
                </div>

                <p className="mt-8 text-center text-sm text-brand-ash">
                    Need another version?{" "}
                    <a
                        href="https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-green underline underline-offset-4 hover:text-brand-ice"
                    >
                        View all releases on GitHub
                    </a>
                </p>
            </div>
        </section>
    );
}