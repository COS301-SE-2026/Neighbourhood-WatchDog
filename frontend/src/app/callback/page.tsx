"use client";

import { useSearchParams } from "next/navigation";

export default function CallbackPage() {
  const params = useSearchParams();
  const code = params.get("code");

  return (
    <div>
      <h1>Callback Page</h1>
      <p>Auth code:</p>
      <pre>{code}</pre>
    </div>
  );
}