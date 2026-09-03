"use-client"


import Image from "next/image"
import { Button } from "@/components/ui/button";
import Pointer from "@/components/Pointer";
import deisgnImage1 from "@/assets/images/heroImage1.png"
import designImage2 from "@/assets/images/heroImage2.png"
import {motion, useAnimate} from 'framer-motion'
import { useEffect } from "react";

export default function Hero() {
    const [leftDesignScope, leftDesignAnimate] = useAnimate();
    const [leftPointerScope, leftPointerAnimate] = useAnimate();
    const [rightDesignScope, rightDesignAnimate] = useAnimate();
    const [rightPointerScope, rightPointerAnimate] = useAnimate();


    useEffect(() => {
        leftDesignAnimate([
            [leftDesignScope.current, {opacity: 1}, {duration: 0.5}],
            [leftDesignScope.current, {y: 0, x: 0}, {duration: 0.5}]
        ])

        leftPointerAnimate([
            [leftPointerScope.current, {opacity: 1}, {duration: 0.5}],
            [leftPointerScope.current, {y: 0, x: -100}, {duration: 0.5}],
            [leftPointerScope.current, {x: 0, y:[0, 16, 0]}, {duration: 0.5, ease: 'easeInOut'},
        ]
        ])

        rightDesignAnimate([
            [rightDesignScope.current, {opacity: 1}, {duration: 0.5, delay: 1.5}],
            [rightDesignScope.current, {y: 0, x: 0}, {duration: 0.5}]
        ])

        rightPointerAnimate([
            [rightPointerScope.current, {opacity: 1}, {duration: 0.5, delay: 1.5}],
            [rightPointerScope.current, {x: 30, y: 0}, {duration: 0.5}],
            [rightPointerScope.current, {x: -50, y: [0, 20, 0]}, {duration: 0.5, ease: 'easeInOut'},
        ]
        ])
    }, []);
    return (<section className="py-24 overflow-x-clip overflow-y-visible">
        <div className="container mx-auto relative">
            <motion.div initial={{opacity: 0, y: 100, x: -100}} drag ref={leftDesignScope} className="absolute -left-16 top-20 hidden min-[1280px]:block">
                <Image src={designImage2} alt="Design Image 2" draggable="false" width={400} height={200} />
            </motion.div>
            
            <motion.div initial={{opacity:0, y: 100, x: -200}} ref={leftPointerScope} className="absolute left-60 top-62 hidden min-[1280px]:block">
                <Pointer name="Jared" color="slate"/>
            </motion.div>

            <motion.div initial={{opacity: 0, y: 100, x: 100}} drag ref={rightDesignScope} className="absolute -right-25 top-20 min-[1280px]:top-45  hidden min-[1280px]:block">
                <Image src={deisgnImage1} alt="Design Image 1" draggable="false" width={350} height={180} />
            </motion.div>

            <motion.div initial={{opacity:0, x: 120, y: 100}} ref={rightPointerScope} className="absolute right-55 top-120 min-[1280px]:top-55 hidden min-[1280px]:block">
                <Pointer name="Zizou" color="emerald"/>
            </motion.div>
            <div className="flex justify-center">
                <div className="inline-flex py-1 px-3 bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full text-brand-void font-semibold text-sm">
                    Powered by Computer Vision AI
                </div>
            </div>
            <h1 className="text-4xl md:text-6xl sm:text-5xl lg:text-8xl font-medium text-center mt-6 text-balance">
                Your Neighbourhood, <br/>Watched.
            </h1>
            <p className="text-center text-xl text-brand-ash mt-8 max-w-2xl mx-auto">
                From live camera feeds to instant alerts, 
                Neighbourhood WatchDog gives your community 
                real-time visibility and peace of mind, 
                powered by AI that never sleeps.
            </p>
            <form className="flex border border-brand-gunmetal/20 rounded-full p-2 mt-8 max-w-lg mx-auto">
                <input 
                    type="email" 
                    placeholder="Enter your email" 
                    className="bg-transparent px-4 md:flex-1 w-full"
                />
                <Button variant="default" className="whitespace-nowrap rounded-full" size="xs">Sign Up</Button>
            </form>
        </div>
    </section>
    );
}