"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { confirmSignUp, isAuthenticated, resendConfirmationCode } from "@/lib/auth/cognito";
import { ConfirmCard } from "@/components/auth-components/confirm-card";

export default function ConfirmPage() {
  const router = useRouter();

  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // fill email automatically if inside query params
  useEffect(() => {
    const emailFromLogin = searchParams.get("email");

    if (emailFromLogin) {
      setEmail(emailFromLogin);
    }
  }, [searchParams]);

  //already authenticated
  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [router]);

  // clear resend success 
  useEffect(() => {
    if (resendSuccess) {
      const timer = setTimeout(() => {
        setResendSuccess(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [resendSuccess]);

  const handleConfirm = async () => {
    // Reset states
    setError(null);
    setSuccess(false);

    // Validation
    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    if (!code.trim()) {
      setError("Please enter the confirmation code");
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    // must be 6 digit
    if (!/^\d{6}$/.test(code.trim())) {
      setError("Please enter a valid 6-digit confirmation code");
      return;
    }

    setIsLoading(true);

    try {
      await confirmSignUp(email.trim(), code.trim());
      
      setSuccess(true);
      
      // clear data
      setCode("");
      
      // login redirect
      setTimeout(() => {
        router.push("/auth/login");
      }, 2000);
      
    } catch (err) {
      //error message
      let errorMessage = "Confirmation failed. Please try again.";
      
      if (err instanceof Error) {
        // Check for specific Cognito errors
        if (err.message.includes("CodeMismatchException") || err.message.includes("Invalid code")) {            //invalid
          errorMessage = "Invalid confirmation code. Please check and try again.";
        } else if (err.message.includes("ExpiredCodeException") || err.message.includes("expired")) {           //expired
          errorMessage = "This confirmation code has expired. Please request a new one.";
        } else if (err.message.includes("UserNotFoundException") || err.message.includes("not found")) {        //email no exists
          errorMessage = "No account found with this email. Please sign up first.";
        } else if (err.message.includes("Already confirmed") || err.message.includes("already verified")) {     //email verified already
          errorMessage = "This account is already confirmed. Please login instead.";
        } else {                                                                                                //show message atp
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      console.error("Confirmation error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle resend code
  const handleResendCode = async () => {
    // Reset states
    setError(null);
    setResendSuccess(false);

    // Validate email
    if (!email.trim()) {
      setError("Please enter your email address to resend the code");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setIsResending(true);

    try {
      await resendConfirmationCode(email.trim());
      
      setResendSuccess(true);
      setError(null);
      
    } catch (err) {
      // error message
      let errorMessage = "Failed to resend code. Please try again.";
      
      if (err instanceof Error) {
        if (err.message.includes("UserNotFoundException") || err.message.includes("not found")) {               //no account 
          errorMessage = "No account found with this email. Please sign up first.";
        } else if (err.message.includes("Already confirmed") || err.message.includes("already verified")) {     //account confirmed already
          errorMessage = "This account is already confirmed. Please login instead.";
        } else {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      console.error("Resend error:", err);
    } finally {
      setIsResending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading && !success) {
      handleConfirm();
    }
  };

  return (
    <ConfirmCard
      email={email}
      setEmail={setEmail}
      code={code}
      setCode={setCode}
      onSubmit={handleConfirm}
      onResendCode={handleResendCode}
      onKeyDown={handleKeyDown}
      isLoading={isLoading}
      isResending={isResending}
      error={error}
      success={success}
      resendSuccess={resendSuccess}
    />
  );
}