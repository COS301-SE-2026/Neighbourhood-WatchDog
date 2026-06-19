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
import { Loader2 } from "lucide-react";

type ConfirmCardProps = {
  className?: string;

  email: string;
  setEmail: (v: string) => void;

  code: string;
  setCode: (v: string) => void;

  onSubmit: () => void;
  onResendCode: () => void;  // Separate prop for resend
  onKeyDown?: (e: React.KeyboardEvent) => void;
  isLoading?: boolean;
  isResending?: boolean;  // Separate loading for resend
  error?: string | null;
  success?: boolean;
  resendSuccess?: boolean;  // Success state for resend
};

export function ConfirmCard({
  className,
  email,
  setEmail,
  code,
  setCode,
  onSubmit,
  onResendCode,
  onKeyDown,
  isLoading = false,
  isResending = false,
  error = null,
  success = false,
  resendSuccess = false,
}: ConfirmCardProps) {
  return (
    <Card
      className={cn(
        "w-full max-w-lg sm:max-w-xl p-2 sm:p-4 rounded-2xl border border-navy/12 bg-white/95 shadow-xl backdrop-blur",
        className
      )}
    >
      <CardHeader className="space-y-3">
        <CardTitle className="text-[2rem] sm:text-[2.5rem] font-bold tracking-tight text-navy">
          Verify Your Email
        </CardTitle>

        <CardDescription className="text-base text-body">
          Enter the 6-digit confirmation code sent to your email
        </CardDescription>

        <CardAction>
          <Link href="/auth/login" passHref>
            <Button variant="link" className="text-sm font-medium">
              Already verified? Login
            </Button>
          </Link>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Success message for confirmation */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            Email confirmed successfully! Redirecting to login...
          </div>
        )}

        {/* Success message for resend */}
        {resendSuccess && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            New confirmation code sent to your email!
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-6">
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
              placeholder="m@example.com"
              disabled={isLoading || success}
              className="h-11 text-base"
              required
            />
          </div>

          {/* CONFIRMATION CODE */}
          <div className="grid gap-2">
            <Label htmlFor="code" className="text-sm font-medium">
              Confirmation Code
            </Label>
            <Input
              id="code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Enter 6-digit code"
              disabled={isLoading || success}
              className="h-11 text-base tracking-widest font-mono"
              maxLength={6}
              required
            />
            <p className="text-xs text-gray-500">
              Check your email for the confirmation code
            </p>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex-col gap-3 pt-2">
        {/* Verify */}
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isLoading || success}
          className="w-full h-11 text-base font-medium bg-navy text-white hover:bg-steel transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Verifying...
            </>
          ) : success ? (
            "Verified!"
          ) : (
            "Verify Email"
          )}
        </Button>

        {/* Resend code */}
        <div className="flex flex-col items-center gap-1 w-full">
          <p className="text-sm text-gray-500">
            Didn't receive the code?
          </p>
          <Button
            type="button"
            onClick={onResendCode}
            disabled={isLoading || isResending || success}
            variant="link"
            className="text-sm text-sky-600 hover:text-sky-800"
          >
            {isResending ? (
              <>
                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                Sending...
              </>
            ) : (
              "Resend confirmation code"
            )}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}