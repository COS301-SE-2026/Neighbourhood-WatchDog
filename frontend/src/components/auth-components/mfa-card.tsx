"use client";

import { useState } from "react";

interface MfaCardProps {
  destination: string;
  onVerify: (code: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function MfaCard({
  destination,
  onVerify,
  isLoading,
  error,
}: MfaCardProps) {

  const [code, setCode] = useState("");

  const handleSubmit = () => {
    if (!code.trim()) return;

    onVerify(code);
  };


  return (
    <div>
      <h2>
        Verify your email
      </h2>

      <p>
        Enter the code sent to {destination}
      </p>


      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="123456"
        maxLength={6}
      />


      {error && (
        <p>
          {error}
        </p>
      )}


      <button
        onClick={handleSubmit}
        disabled={isLoading}
      >
        {isLoading ? "Verifying..." : "Verify"}
      </button>

    </div>
  );
}