"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { login, setSession, isAuthenticated, verifyMfa } from "@/lib/auth/cognito";
import { LoginCard } from "@/components/auth-components/login-card";


export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false); 
  const [error, setError] = useState<string | null>(null);

  // mfa states
  const [showMfa, setShowMfa] = useState(false);
  const [mfaSession, setMfaSession] = useState("");
  const [mfaDestination, setMfaDestination] = useState("");

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
      const result = await login(email.trim(), password);

      if (result.mfaRequired) {

        setMfaSession(result.session ?? "");

        setMfaDestination(
          result.delivery?.destination ?? ""
        );

        setShowMfa(true);

        return;
      }


      // Normal login
      setSession({
        accessToken: result.accessToken!,
        idToken: result.idToken!,
        expiresIn: result.expiresIn,
      });

      setPassword("");

      router.push("/dashboard");
      
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

  const handleMfaVerify = async (code: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const tokens = await verifyMfa(
        email.trim(),
        mfaSession,
        code
      );

      setSession(tokens);

      setPassword("");

      router.push("/dashboard");

    } catch (err) {

      const errorMessage = err instanceof Error
        ? err.message
        : "Invalid verification code.";

      setError(errorMessage);

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
    <>
      {!showMfa ? (
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
      ) : (
        <MfaCard
          destination={mfaDestination}
          onVerify={handleMfaVerify}
          isLoading={isLoading}
          error={error}
        />
      )}
    </>
  );
}