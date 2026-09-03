import { HTMLAttributes } from "react";
import { twMerge } from "tailwind-merge";

export default function Key(props: HTMLAttributes<HTMLElement>) {
    const {className, children, ...otherProps} = props;
    return(
        <div className={twMerge("size-14 bg-brand-gunmetal inline-flex items-center justify-center rounded-2xl text-xl text-brand-void font-medium", className)} {...otherProps}>
            {children}
        </div>
    );
};