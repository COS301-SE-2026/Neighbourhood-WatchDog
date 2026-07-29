"use client"

import Tag from "@/components/Tag";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
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

    const [selectedIndex, setselectedIndex] = useState(0);
    return (
        <section id="faqs" className="py-24">
            <div className="container mx-auto px-5 sm:px-6">
                <div className="flex justify-center">
                    <Tag>Faqs</Tag>
                </div>
                <h2 className="text-5xl font-medium mt-6 text-center max-w-xl mx-auto">
                    Questions? We&apos;ve got <span className="text-emerald-400">answers</span>
                </h2>
                <div className="mt-12 flex flex-col gap-6 max-w-xl mx-auto">
                    {faqs.map((faq, faqIndex) =>(
                        <div key={faq.question} className="bg-neutral-900 rounded-2xl border border-white/10 p-6">
                            <button className="flex w-full justify-between items-center" onClick={() => setselectedIndex(faqIndex)}>
                                <h3 className="font-medium">{faq.question}</h3>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={twMerge("feather feather-plus text-emerald-400 flex-shrink-0 transition duration-300", selectedIndex === faqIndex && "rotate-45")}><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                            </button>
                            <AnimatePresence>
                                {selectedIndex === faqIndex && (
                                    <motion.div initial={{height: 0, marginTop: 0,}} animate={{height: "auto", marginTop:24}} exit={{height: 0, marginTop: 0}} className={twMerge("overflow-hidden")}>
                                        <p className="text-white/50">{faq.answer}</p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                            
                        </div>
                    ))}
                </div>
            </div>
            
        </section>
    );
}