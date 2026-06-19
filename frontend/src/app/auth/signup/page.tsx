"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { signUp, isAuthenticated } from "@/lib/auth/cognito";
import { SignupCard } from "../../../components/auth-components/signup-card";

export default function SignupPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [router]);

  const handleSignUp = async () => {
    // Reset states
    setError(null);
    setSuccess(false);

    // Validation
    if (!name.trim() || !address.trim() || !email.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setIsLoading(true);

    try {
      await signUp(email, password, name, address);
      
      // success state
      setSuccess(true);
      
      //clear data
      setPassword("");
      setConfirmPassword("");
      
      // Redirect to confirmation afterr delay
      setTimeout(() => {
        router.push("/confirm");
      }, 2000);
      
    } catch (err) {
      //error message
      let errorMessage = "Signup failed. Please try again.";
      
      if (err instanceof Error) {
        // Check for cognito errors
        if (err.message.includes("UsernameExistsException") || err.message.includes("already exists")) {//account exits already
          errorMessage = "An account with this email already exists. Please login instead.";
        } else if (err.message.includes("InvalidPasswordException")) {                                  //invalid password
          errorMessage = "Password does not meet requirements. Please use at least 8 characters with numbers and special characters.";
        } else if (err.message.includes("InvalidParameterException")) {                                 //invlaid inputs
          errorMessage = "Please check your information and try again.";
        } else {                                                                                        //just show message at this point
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      console.error("Signup error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleSignUp();
    }
  };

  return (
    <SignupCard
      name={name}
      setName={setName}
      email={email}
      setEmail={setEmail}
      password={password}
      setPassword={setPassword}
      confirmPassword={confirmPassword}
      setConfirmPassword={setConfirmPassword}
      address={address}
      setAddress={setAddress}
      onSubmit={handleSignUp}
      onKeyDown={handleKeyDown}
      isLoading={isLoading}
      error={error}
    />
  );
}