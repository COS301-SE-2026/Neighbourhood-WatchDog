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
    const wordIndex = useTransform(scrollYProgress, [0.12, 0.78], [0, words.length]);

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
            <Tag>
              <span className="sm:hidden">Introducing WatchDog</span>
              <span className="hidden sm:inline">Introducing Neighbourhood WatchDog</span>
            </Tag>
          </div>

          <div className="mx-auto mt-10 max-w-6xl px-4 text-center text-3xl font-medium leading-[1.15] sm:text-4xl lg:text-6xl">
            <span>Your neighbourhood deserves better security.</span>{" "}

            <span className="text-brand-frost/35">
              {words.map((word, index) => (
                <span
                  key={`${word}-${index}`}
                  className={twMerge(
                    "text-brand-frost/35 transition-colors duration-300",
                    index < currentWord && "text-brand-frost"
                  )}
                >
                  {word}{" "}
                </span>
              ))}
            </span>

            <span
              className={twMerge(
                "mt-6 block text-3xl text-brand-green transition-opacity duration-500 sm:text-4xl lg:text-5xl",
                currentWord >= words.length ? "opacity-100" : "opacity-0"
              )}
            >
              That&apos;s why we built Neighbourhood WatchDog.
            </span>
          </div>
        </div>

        <div className="h-[90vh] lg:h-[110vh]" />
      </div>
    </section>);
}