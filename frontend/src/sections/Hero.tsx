import Image from "next/image"
import { Button } from "@/components/ui/button";
import Pointer from "@/components/Pointer";
import deisgnImage1 from "@/assets/images/heroImage1.png"
import designImage2 from "@/assets/images/heroImage2.png"

export default function Hero() {
    return (<section className="py-24 overflow-x-clip">
        <div className="container mx-auto relative">
            <div className="absolute -left-42 top-20 hidden lg:block">
                <Image 
                    src={designImage2} 
                    alt="Design Image 2"
                    width={400}
                    height={200}
                />
            </div>

            <div className="absolute -right-64 top-4 hidden lg:block">
                <Image 
                    src={deisgnImage1} 
                    alt="Design Image 1"
                    width={400}
                    height={200}
                />
            </div>

            <div className="absolute -left-0 top-62 hidden lg:block">
                <Pointer name="Jared" color="slate"/>
            </div>

            <div className="absolute -right-0 top-115 hidden lg:block">
                <Pointer name="Zizou" color="emerald"/>
            </div>
            <div className="flex justify-center">
                <div className="inline-flex py-1 px-3 bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full text-black font-semibold text-sm">
                    Powered by Computer Vision AI
                </div>
            </div>
            <h1 className="text-4xl md:text-6xl sm:text-5xl lg:text-8xl font-medium text-center mt-6 text-balance">
                Your Neighbourhood. Watched.
            </h1>
            <p className="text-center text-xl text-white/50 mt-8 max-w-2xl mx-auto">
                From live camera feeds to instant alerts, 
                Neighbourhood WatchDog gives your community 
                real-time visibility and peace of mind, 
                powered by AI that never sleeps.
            </p>
            <form className="flex border border-white/15 rounded-full p-2 mt-8 max-w-lg mx-auto">
                <input 
                    type="email" 
                    placeholder="Enter your email" 
                    className="bg-transparent px-4 md:flex-1"
                />
                <Button variant="default" className="whitespace-nowrap rounded-full" size="xs">Sign Up</Button>
            </form>
        </div>
    </section>
    );
}