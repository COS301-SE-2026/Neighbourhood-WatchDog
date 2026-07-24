"use client"

import Navbar from "@/sections/Navbar";
import Hero from "@/sections/Hero";
import Introduction from "@/sections/Introduction";
import Features from "@/sections/Features";
import Integrations from "@/sections/Integrations";
import Faqs from "@/sections/Faqs";
import Footer from "@/sections/Footer";

export default function Home() {
    return (
        <>
            <Navbar/>
            <Hero/>
            <Introduction/>
            <Features/>
            <Integrations/>
            <Faqs/>
            <Footer/>
        </>
    );

}