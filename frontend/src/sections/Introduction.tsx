import Tag from "@/components/Tag"

const text = "Cameras record everything, but nobody's watching. Footage sits unreviewed until something already went wrong, and by then it's too late to stop it."

export default function Introduction() {
    return (
        <section className="py-28 lg:py-40">
            <div className="container mx-auto">
                <div className="flex justify-center">
                    <Tag>Introducing Neighbourhood WatchDog</Tag>
                </div>
                <div className="text-4xl md:6xl lg:text-7xl text-center font-medium mt-10">
                    <span>Your neighbourhood deserves better security.</span>{" "}
                    <span className="text-white/15">{text}</span>
                    <span className="text-emerald-400 block">That&apos;s why we built Neighbourhood WatchDog.</span>
                </div>
                

            </div>
        </section>
    )
}