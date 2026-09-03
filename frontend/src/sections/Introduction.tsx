"use client";

import Tag from "@/components/Tag"
import { useScroll, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { twMerge } from "tailwind-merge";
const text = "Cameras record everything, but nobody's watching. Footage sits unreviewed until something already went wrong, and by then it's too late to stop it."
const words = text.split(' ');
export default function Introduction() {
    const scrollTarget = useRef<HTMLDivElement>(null);
    const {scrollYProgress} = useScroll({target: scrollTarget, offset: ['start end', 'end end']})
    const [currentWord, setCurrentWord] = useState(0);
    const wordIndex = useTransform(scrollYProgress, [0, 1], [0, words.length])

    useEffect(() => {
        const unsubscribe = wordIndex.on("change", (latest) => {
        setCurrentWord(Math.floor(latest));
        });

        return unsubscribe;
    }, [wordIndex]);
     return (
    <section ref={scrollTarget} className="py-28 lg:py-40">
      <div className="container mx-auto">
        <div className="sticky top-24">
          <div className="flex justify-center">
            <Tag>Introducing Neighbourhood WatchDog</Tag>
          </div>

          <div className="mt-10 text-center text-2xl font-medium md:text-5xl lg:text-7xl">
            <span>Your neighbourhood deserves better security.</span>{" "}

            <span className="text-brand-frost/15">
              {words.map((word, index) => (
                <span
                  key={`${word}-${index}`}
                  className={twMerge("transition duration-500 text-brand-frost/15", index < currentWord && "text-brand-frost")}
                >
                  {word}{" "}
                </span>
              ))}
            </span>

            <span className="block text-brand-green">
              That&apos;s why we built Neighbourhood WatchDog.
            </span>
          </div>
        </div>

        <div className="h-[150vh]" />
      </div>
    </section>);
}