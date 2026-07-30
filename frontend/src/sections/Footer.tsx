import logoImage from '@/assets/images/logo-mark-only.svg'
import Image from 'next/image';

const footLinks = [
    {label:"Contact", href:"#contact"},
    {label:"Privacy Policy", href:"#policy"},
    {label:"Terms & Conditions", href:"#terms"},
]
export default function Footer() {
    return (
        <section className='py-16'>
            <div className="container mx-auto lg:px-24">
                <div className='flex flex-col md:flex-row items-center md:justify-between gap-6'>
                    <div className='flex gap-2 items-center'>
                        <Image src={logoImage} alt={"Neighbourhood Watchdog logo"} className="h-9 w-auto ml-2" />
                        <span className="font-bold text-lg">Watchdog</span>
                    </div>

                    <div>
                        <nav className='flex flex-wrap justify-center gap-4 sm:gap-6'>
                            {footLinks.map((link) => (
                                <a key={link.label} href={link.href} className='text-white/50 text-sm'>
                                    {link.label}
                                </a>
                            ))}
                        </nav>
                    </div>
                </div>
            </div>
        </section>
    );
}