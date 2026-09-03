import { HTMLAttributes } from "react";
import { twMerge } from "tailwind-merge";

export default function Avatar (props: HTMLAttributes<HTMLElement>) {
    const {className, children, ...otherProps} = props
    return (
        <div className={twMerge("size-20 rounded-full overflow-hidden border-4 border-brand-pulse p-1 bg-brand-depth", className)} {...otherProps}>
            {children}
        </div>
    );
}