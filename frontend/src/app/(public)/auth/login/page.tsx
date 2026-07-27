"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { login, setSession, isAuthenticated } from "@/lib/auth/cognito";
import { LoginCard } from "@/components/auth-components/login-card";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false); 
  const [error, setError] = useState<string | null>(null);

  //Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [router]);

  const handleLogin = async () => {
    // Reset states
    setError(null);

    // Did the user enter both the email and password
    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password");
      return;
    }

    setIsLoading(true);//Now we make the call // Let the user know with the spinner

    try {
      const tokens = await login(email.trim(), password);// API call returns the tokens
      
      // Store session
      setSession(tokens);
      
      // Clear sensitive data (password)
      setPassword("");
      
      // Navigate to dashboard
      router.push("/dashboard");
    } catch (err) {
      //error message
      const errorMessage = err instanceof Error 
        ? err.message 
        : "Invalid email or password. Please try again.";
      
      setError(errorMessage);
      console.error("Login error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  //Enter key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleLogin();
    }
  };

  return (

      <LoginCard
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        onSubmit={handleLogin}
        onKeyDown={handleKeyDown}
        isLoading={isLoading}
        error={error}
      />
  );
}