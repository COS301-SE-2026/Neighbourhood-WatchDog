import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { Loader2, Eye, EyeOff } from "lucide-react";

type SignupCardProps = {
  className?: string;

  firstName: string;
  setFirstName: (v: string) => void;

  lastName: string;
  setLastName: (v: string) => void;

  address: string;
  setAddress: (v: string) => void;

  email: string;
  setEmail: (v: string) => void;

  password: string;
  setPassword: (v: string) => void;

  confirmPassword: string;
  setConfirmPassword: (v: string) => void;

  onSubmit: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;//Enter key logic
  isLoading?: boolean;
  error?: string | null;
};

export function SignupCard({
  className,
  firstName,
  setFirstName,
  lastName,
  setLastName,
  address,
  setAddress,
  email,
  setEmail,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  onSubmit,
  onKeyDown,
  isLoading = false,
  error = null,
}: SignupCardProps) {
  // Password visibility toggle
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <Card
      className={cn(
        "w-full max-w-lg sm:max-w-2xl p-2 sm:p-4 rounded-2xl border border-navy/12 bg-white/95 shadow-xl backdrop-blur",
        className
      )}
    >
      <CardHeader className="space-y-3">
        <CardTitle className="text-[2rem] sm:text-[2.5rem] font-bold tracking-tight text-navy">
          Create Account
        </CardTitle>

        <CardDescription className="text-base text-body">
          Enter your details below to get started
        </CardDescription>

        <CardAction>
          <Link href="/auth/login" passHref>
            <Button variant="link" className="text-sm font-medium">
              Already have an account? Login
            </Button>
          </Link>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-6">
          {/* first and last name */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="firstName" className="text-sm font-medium">
                First Name
              </Label>

              <Input
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="First Name"
                disabled={isLoading}
                className="h-11 text-base"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="lastName" className="text-sm font-medium">
                Last Name
              </Label>

              <Input
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Last Name"
                disabled={isLoading}
                className="h-11 text-base"
                required
              />
            </div>
          </div>

          {/* ADDRESS */}
          <div className="grid gap-2">
            <Label htmlFor="address" className="text-sm font-medium">
              Address
            </Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder=" 44 Home Street, Pretoria"
              disabled={isLoading}
              className="h-11 text-base"
              required
            />
          </div>

          {/* EMAIL */}
          <div className="grid gap-2">
            <Label htmlFor="email" className="text-sm font-medium">
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="email@example.com"
              disabled={isLoading}
              className="h-11 text-base"
              required
            />
          </div>

          {/* PASSWORD with visibility toggle */}
          <div className="grid gap-2">
            <Label htmlFor="password" className="text-sm font-medium">
              Password
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={isLoading}
                className="h-11 text-base pr-10"
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500">Must have: 8+ characters | Special Character | Number</p>
          </div>

          {/* CONFIRM PASSWORD with visibility toggle */}
          <div className="grid gap-2">
            <Label htmlFor="confirmPassword" className="text-sm font-medium">
              Confirm Password
            </Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={isLoading}
                className="h-11 text-base pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={isLoading}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex-col gap-3 pt-2">
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isLoading}
          className="w-full h-11 text-base font-medium bg-navy text-white hover:bg-steel transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating account...
            </>
          ) : (
            "Create Account"
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}