import type { CamerasType } from "@/sections/Integrations";
import Image from "next/image";
import { twMerge } from "tailwind-merge";

export default function CameraColumn(props: {
    cameras: CamerasType;
    className?: string;

}) {
    const {cameras, className} = props;
    return(
        <div className={twMerge("flex flex-col gap-4 pb-4", className)}>
            {cameras.map(camera => (
                <div key={camera.name} className="bg-neutral-900 border border-white/10 rounded-3xl p-6">
                    <div className="flex justify-center">
                        <Image 
                            src={camera.icon} 
                            alt={`${camera.name} icon`}
                            className="size-24"
                        />
                    </div>
                    <h3 className="text-3xl text-center mt-6">{camera.name}</h3>
                    <p className="text-center text-white/50 mt-2">{camera.description}</p>
                </div>
            ))}
        </div>
    );
}