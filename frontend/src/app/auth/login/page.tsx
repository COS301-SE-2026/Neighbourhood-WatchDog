"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { login, setSession } from "@/lib/auth/cognito";
import { LoginCard } from "../../../components/auth-components/login-card";

export default function Page() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const tokens = await login(email, password);

      // store session
      setSession(tokens);

      // go to protected area
      router.push("/dashboard");
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  return (
    <LoginCard
      email={email}
      setEmail={setEmail}
      password={password}
      setPassword={setPassword}
      onSubmit={handleLogin}
    />
  );
}