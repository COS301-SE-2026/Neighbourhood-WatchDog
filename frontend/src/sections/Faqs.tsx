"use client"

import { useState } from "react";
import Tag from "@/components/Tag";
import { twMerge } from "tailwind-merge";

const faqs = [
    {
        question: "Do I need to install new cameras?",
        answer:
        "No. WatchDog connects to your neighbourhood's existing CCTV infrastructure, so there's no need to replace or add new hardware. Our AI simply plugs into the camera feeds you already have.",
    },
    {
        question: "How does WatchDog know what's actually a threat?",
        answer:
        "WatchDog uses real-time computer vision to detect human presence and classify behaviour, loitering, perimeter scanning, and unusual movement, and tracks individuals across multiple cameras instead of treating each feed in isolation.",
    },
    {
        question: "Who can see alerts and footage?",
        answer:
        "Access is role-based. Residents, security officers, neighbourhood admins, and system admins each see only what's relevant to their role, so sensitive footage and alerts aren't exposed to everyone.",
    },
    {
        question: "How fast are alerts sent when something is detected?",
        answer:
        "Alerts are pushed in real time the moment a detection event occurs, so your security officers and admins are notified within seconds, not after someone reviews footage later.",
    },
    {
        question: "Is our neighbourhood's data kept private from other neighbourhoods?",
        answer:
        "Yes. Every neighbourhood's data is isolated at the database level, so footage, alerts, and risk scores from one community are never visible to another.",
    },
    ]

export default function Faqs() {

    const [selectedIndex, setSelectedIndex] = useState<number | null>(0);

    const handleQuestionClick = (faqIndex: number) => {

        setSelectedIndex((currentIndex) =>
            currentIndex === faqIndex ? null : faqIndex
        );

    }
    return (
        <section className="py-24">
            <div className="container mx-auto">
                <div className="flex justify-center">
                    <Tag>Faqs</Tag>
                </div>
                <h2 className="text-6xl font-medium mt-6 text-center max-w-xl mx-auto">
                    Questions? We&apos;ve got <span className="text-emerald-400">answers</span>
                </h2>

                <p className="mx-auto mt-4 max-w-2x1 text-center text-white/50">
                    Learn more about cameras, live monitoring, AI-assisted detections, 
                    access control, and common troubleshooting steps.
                </p>

                <div className="mt-12 flex flex-col gap-6 max-w-xl mx-auto">
                    {faqs.map((faq, faqIndex) =>{
                        const isSelected = selectedIndex === faqIndex;
                        const answerId = `faq-answer-${faqIndex}`;

                        return (
                            <div key={faq.question} className="rounded-2x1 border border-white/10 bg-neutral-900 p-6">
                                <button type="button" onClick={() => handleQuestionClick(faqIndex)} aria-expanded={isSelected} aria-controls={answerId} className="flex w-full items-center justify-between gap-4 text-left">
                                    <h3 className="font-medium">{faq.question}</h3>

                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="24"
                                        height="24"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        aria-hidden="true"
                                        className={twMerge(
                                        "shrink-0 text-emerald-400 transition-transform duration-200",
                                        isSelected && "rotate-45",
                                        )}>  
                                        <line x1="12" y1="5" x2="12" y2="19" />
                                        <line x1="5" y1="12" x2="19" y2="12" />
                                    </svg>
                                </button>

                                {isSelected && (
                                    <div id={answerId} className="mt-5">
                                        <p className="leading-7 text-white/50">{faq.answer}</p>
                                    </div>
                                )}
                            </div>
                        );
                        
                    //     <div key={faq.question} className="bg-neutral-900 rounded-2xl border border-white/10 p-6">
                    //         <div className="flex justify-between items-center">
                    //             <h3 className="font-medium">{faq.question}</h3>
                    //             <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={twMerge("feather feather-plus text-emerald-400 flex-shrink-0", selectedIndex === faqIndex && "rotate-45")}><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    //         </div>
                    //         <div className={twMerge("mt-6", selectedIndex !== faqIndex && "hidden")}>
                    //             <p className="text-white/50">{faq.answer}</p>
                    //         </div>
                    //     </div>
                    // )
                    })}
                </div>
            </div>
            
        </section>
    );
}