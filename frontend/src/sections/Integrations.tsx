import CameraColumn from "@/components/CamerasColumn";
import Tag from "@/components/Tag";

import tapoImage from "@/assets/images/tapo.svg"
import foscamImage from "@/assets/images/foscam.svg"
import wyzeImage from "@/assets/images/wyze.svg"
import amcrestImage from "@/assets/images/amcrest.svg"
import dahuaImage from "@/assets/images/dahua.svg"
import reolinkImage from "@/assets/images/reolink.svg"

const cameras = [
    {name: "Tapo", icon: tapoImage, description: "Budget cameras that support local streaming (no cloud needed)"},
    {name: "Foscam", icon: foscamImage, description: "Local video access with reliable long-term support"},
    {name: "Wyze", icon: wyzeImage, description: "Affordable cams, local streaming via free firmware update"},
    {name: "Amcrest", icon: amcrestImage, description: "Local streaming and works with most NVR software"},
    {name: "Dahua", icon: dahuaImage, description: "Professional-grade cameras with local, cloud-free access"},
    {name: "Reolink", icon: reolinkImage, description: "Local streaming out of the box, widely NVR-compatible"},
]

export type CamerasType = typeof cameras;

export default function Integrations() {
    return (
        <section className="py-24 overflow-hidden">
            <div className="container mx-auto">
                <div className="grid lg:grid-cols-2 items-center lg:gap-16">
                    <div>
                        <Tag>Cameras</Tag>
                        <h2 className="text-6xl font-medium mt-6">
                            Works with different <span className="text-emerald-400">cameras</span>
                        </h2>
                        <p className="text-white/50 mt-4 text-lg">
                            seamlessly connect with different cameras,
                            we&apos;ve made it easy, connect your camera 
                            and your stream is up and running.
                        </p>
                    </div>

                    <div>
                        <div className="h-[400px] lg:h-[800px] mt-8 lg:mt-0 overflow-hidden grid md:grid-cols-2 gap-4 [mask-image:linear-gradient(to_bottom, transparent,black_10%,black_90%,transparent)]">
                            <CameraColumn cameras={cameras}/>
                            <CameraColumn cameras={cameras.slice().reverse()} className="hidden md:flex"/>
                        </div>
                    </div>
                </div>

            </div>
        </section>
    );
};