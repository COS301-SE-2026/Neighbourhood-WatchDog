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

type SignupCardProps = {
  className?: string;

  name: string;
  setName: (v: string) => void;

  address: string;
  setAddress: (v: string) => void;

  email: string;
  setEmail: (v: string) => void;

  password: string;
  setPassword: (v: string) => void;

  confirmPassword: string;
  setConfirmPassword: (v: string) => void;

  onSubmit: () => void;
};

export function SignupCard({
  className,
  name,
  setName,
  address,
  setAddress,
  email,
  setEmail,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  onSubmit,
}: SignupCardProps) {
  return (
    <Card
      className={cn(
        "w-full max-w-md sm:max-w-xl rounded-3xl border border-[rgba(29,42,94,0.12)] bg-white/95 shadow-[0_20px_60px_rgba(29,42,94,0.14)] backdrop-blur",
        className
      )}
    >
      <CardHeader>
        <CardTitle className="text-3xl sm:text-4xl font-semibold tracking-tight text-[color:var(--color-navy)]">
          Create your account
        </CardTitle>

        <CardDescription className="text-base text-[color:var(--color-body)]">
          Enter your details below to sign up
        </CardDescription>

        <CardAction>
          <Button variant="link">Login</Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col gap-6">

          {/* NAME */}
          <div className="grid gap-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>

          {/* ADDRESS */}
          <div className="grid gap-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Pretoria, South Africa"
              required
            />
          </div>

          {/* EMAIL */}
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="m@example.com"
              required
            />
          </div>

          {/* PASSWORD */}
          <div className="grid gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {/* CONFIRM PASSWORD */}
          <div className="grid gap-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

        </div>
      </CardContent>

      <CardFooter className="flex-col gap-2">
        <Button
          type="button"
          onClick={onSubmit}
          className="w-full bg-[color:var(--color-navy)] text-white hover:bg-[color:var(--color-steel)]"
        >
          Sign Up
        </Button>
      </CardFooter>
    </Card>
  );
}