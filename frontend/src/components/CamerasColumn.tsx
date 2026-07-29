"use client"

import type { CamerasType } from "@/sections/Integrations";
import Image from "next/image";
import { twMerge } from "tailwind-merge";
import {motion} from 'framer-motion'
import { Fragment } from "react/jsx-runtime";

export default function CameraColumn(props: {
    cameras: CamerasType;
    className?: string;
    reverse?: boolean;

}) {
    const {cameras, className, reverse} = props;
    return(
        <motion.div initial={{y: reverse ? "-50%" : 0}} animate={{y: reverse ? 0 : "-50%"}} transition={{duration: 15, repeat: Infinity, ease: 'linear'}} className={twMerge("flex flex-col gap-4 pb-4", className)}>
            {Array.from({length:2}).map((_,i)=>(
                <Fragment key={i}>
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
                </Fragment>
            ))}
            
        </motion.div>
    );
}