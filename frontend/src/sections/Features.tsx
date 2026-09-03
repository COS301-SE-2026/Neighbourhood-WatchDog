import Tag from "@/components/Tag";
import FeatureCard from "@/components/FeatureCard";
import detection3 from "@/assets/images/detection_1.png"
import detection1 from "@/assets/images/detection_2.png"
import detection2 from "@/assets/images/detection_3.png"
import detectionadd from "@/assets/images/add_detection.png"
import Image from "next/image";
import Avatar from "@/components/Avatar";
import Key from "@/components/Key";

const features = [
    "Live Alerts",
    "Multi-Camera Tracking",
    "Loitering Detection",
    "Perimeter Alerts",
    "Historical Trends",
    "Instant Notifications",
    "Secure Data Isolation"
]

export default function Features() {
    return (
        <section className="py-24" id="features">
            <div className="container mx-auto">
                <div className="flex justify-center">
                    <Tag>Features</Tag>
                </div>
                
                <h2 className="text-6xl font-medium text-center mt-6 max-w-2xl mx-auto">
                    Where vigilance meets <span className="text-brand-green">simplicity</span>
                </h2>
                <div className="mt-12 grid grid-cols-1 md:grid-cols-4 lg:grid-cols-3 gap-8 mx-auto">
                    <FeatureCard title="Real-time Threat Detection" description="AI watches every camera feed continuously, 
                                flagging loitering, unusual movement, 
                                and perimeter breaches the instant they happen." className="md:cols-span-3">
                                <div className="aspect-video flex items-center justify-center">
                                    <Avatar className="z-40">
                                        <Image src={detection1} alt="camera image 1" className="rounded-full"/>
                                    </Avatar>

                                    <Avatar className="-ml-6 border-brand-green">
                                        <Image src={detection2} alt="camera image 2"  className="rounded-full"/>
                                    </Avatar>

                                    <Avatar className="-ml-6 border-brand-caution">
                                        <Image src={detection3} alt="camera image 3" className="rounded-full"/>
                                    </Avatar>

                                    <Avatar className="-m1-6 border-transparent">
                                        <Image src={detectionadd} alt="add image 3" className="rounded-full"/>
                                        {/* <div className="size-full bg-brand-slate rounded-full">
                                            {Array.from({length:3}).map((_, i) =>(
                                                <span className="size-1.5 rounded-full bg-brand-depth inline-flex items-center justify-center gap-1" key={i}></span>
                                            ))}
                                        </div> */}
                                    </Avatar>
                            </div>    
                                    
                    </FeatureCard>

                    <FeatureCard title="Neighbourhood Risk Scoring" description="Your neighbourhood's risk level is currently MEDIUM, 
                                calculated automatically from the last 24 hours of activity." className="md:cols-span-3 lg:cols-span-1">
                        <div className="aspect-video flex items-center justify-center">
                            <p className="text-4xl font-extrabold text-brand-frost/20 text-center">
                                Powered by <span className="bg-gradient-to-r from-brand-pulse to-brand-green bg-clip-text text-transparent">Intelligent</span>{" "} threat analysis
                            </p>
                        </div>
                    </FeatureCard>

                    <FeatureCard title="Role-Based Access" description="Residents, security officers, and admins each see exactly what they need, nothing more." className="md:cols-span-3 lg:cols-span-1 md:cols-start-2 lg:cols-start-auto">      
                        <div className="aspect-video flex items-center justify-center gap-4">
                            <Key className="w-28">Admin</Key>
                            <Key className="w-30">Officer</Key>
                            <Key className="w-32">Resident</Key>
                        </div>      
                    </FeatureCard>
                </div>
                <div className="mt-8 flex flex-wrap gap-4 justify-center">
                    {features.map(feature => (
                        <div key={feature} className="bg-brand-depth border border-border inline-flex px-3 md:px-5 md:py-2 py-1.5 rounded-2xl gap-3 items-center">
                            <span className="bg-brand-green text-brand-void size-5 rounded-full inline-flex items-center justify-center text-xl">&#10038;</span>
                            <span className="font-medium md:text-lg">{feature}</span>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
