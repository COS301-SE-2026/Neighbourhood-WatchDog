"use client";

import { useState } from "react";
import { Input } from "./input";

export function PasswordInput(props: any) {
  const [show, setShow] = useState(false);

  return (
    <div className="relative">
      <Input type={show ? "text" : "password"} {...props} />

      <button
        type="button"
        onClick={() => setShow((v) => !v)}
        className="absolute right-3 top-2 text-xs text-gray-400"
      >
        {show ? "Hide" : "Show"}
      </button>
    </div>
  );
}