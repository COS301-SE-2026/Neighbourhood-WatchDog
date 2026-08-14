import { Plus } from "lucide-react";

const exampleCameras = [
    {
        id: "front-gate",
        name: "Front gate",
        location: "Main entrance · 45 Oak Avenue",
        status: "Live",
        statusDotClass: "bg-emerald-400",
        lastActivity: "No recent alerts",
        alerts: 0,
    },
    {
        id: "driveway",
        name: "Driveway",
        location: "North driveway · 45 Oak Avenue",
        status: "Live",
        statusDotClass: "bg-emerald-400",
        lastActivity: "Motion detected 12 min ago",
        alerts: 1,
    },
    {
        id: "back-garden",
        name: "Back garden",
        location: "Rear perimeter · 45 Oak Avenue",
        status: "Offline",
        statusDotClass: "bg-amber-400",
        lastActivity: "Last online 2 hours ago",
        alerts: 0,
    },
];

export default function PropertyCamerasPage() {
    const liveCameraCount = exampleCameras.filter(
        (camera) => camera.status === "Live",
    ).length;

    const offlineCameraCount = exampleCameras.filter(
        (camera) => camera.status === "Offline",
    ).length;

    return (
        <main className="min-h-full w-full bg-black px-6 py-7 text-white md:px-8">
            <div className="max-w-full">
                <header className="mb-7 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-sm text-white/45">
                            Greenfields Estate · 45 Oak Avenue
                        </p>

                        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
                            Cameras
                        </h1>
                    </div>

                    <button
                        type="button"
                        className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-emerald-500 px-3.5 text-sm font-medium text-black transition-colors hover:bg-emerald-400"
                    >
                        <Plus className="size-4" />
                        Add camera
                    </button>
                </header>

                <div className="mb-8 flex flex-wrap items-center gap-x-5 gap-y-2 border-y border-white/10 py-3 text-sm">
                    <span className="text-white/55">
                        <span className="font-medium text-white">
                            {exampleCameras.length}
                        </span>{" "}
                        cameras
                    </span>

                    <span className="flex items-center gap-2 text-white/55">
                        <span className="size-1.5 rounded-full bg-emerald-400" />
                        <span>
                            <span className="font-medium text-white">
                                {liveCameraCount}
                            </span>{" "}
                            live
                        </span>
                    </span>

                    <span className="flex items-center gap-2 text-white/55">
                        <span className="size-1.5 rounded-full bg-amber-400" />
                        <span>
                            <span className="font-medium text-white">
                                {offlineCameraCount}
                            </span>{" "}
                            offline
                        </span>
                    </span>
                </div>

                <section aria-labelledby="camera-feeds-heading">
                    <div className="mb-4">
                        <h2
                            id="camera-feeds-heading"
                            className="text-base font-semibold"
                        >
                            Camera feeds
                        </h2>

                        <p className="mt-1 text-sm text-white/45">
                            Live status and recent activity for this property.
                        </p>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        {exampleCameras.map((camera) => (
                            <article
                                key={camera.id}
                                className="overflow-hidden rounded-lg border border-white/10 bg-[#101011]"
                            >
                                <div className="relative aspect-video bg-[#18181a]">
                                    <div className="absolute left-3 top-3 flex items-center gap-2 text-xs font-medium text-white/75">
                                        <span
                                            className={`size-1.5 rounded-full ${camera.statusDotClass}`}
                                        />
                                        {camera.status}
                                    </div>

                                    <div className="flex h-full items-center justify-center">
                                        <span className="text-xs text-white/25">
                                            Camera feed
                                        </span>
                                    </div>
                                </div>

                                <div className="border-t border-white/10 p-4">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="min-w-0">
                                            <h3 className="truncate text-sm font-semibold text-white">
                                                {camera.name}
                                            </h3>

                                            <p className="mt-1 truncate text-xs text-white/45">
                                                {camera.location}
                                            </p>
                                        </div>

                                        {camera.alerts > 0 && (
                                            <span className="shrink-0 text-xs font-medium text-red-300">
                                                {camera.alerts} unresolved alert
                                                {camera.alerts === 1 ? "" : "s"}
                                            </span>
                                        )}
                                    </div>

                                    <div className="mt-4 border-t border-white/10 pt-3">
                                        <p className="text-xs text-white/45">
                                            {camera.lastActivity}
                                        </p>
                                    </div>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            </div>
        </main>
    );
}