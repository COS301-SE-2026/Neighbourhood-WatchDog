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

type LoginCardProps = {
  className?: string;

  email: string;
  setEmail: (v: string) => void;

  password: string;
  setPassword: (v: string) => void;

  onSubmit: () => void;
};

export function LoginCard({
  className,
  email,
  setEmail,
  password,
  setPassword,
  onSubmit,
}: LoginCardProps) {
  return (
    <Card
      className={cn(
        "w-full max-w-md sm:max-w-xl rounded-xl border border-navy/12 bg-white/95 shadow-lg backdrop-blur",
        className
      )}
    >
      <CardHeader>
        <CardTitle className="text-[2rem] sm:text-[2rem] font-semibold tracking-tight text-navy">
          Login to your account
        </CardTitle>

        <CardDescription className="text-base text-body">
          Enter your email below to login to your account
        </CardDescription>

        <CardAction>
          <Button variant="link">Sign Up</Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col gap-6">

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

        </div>
      </CardContent>

      <CardFooter className="flex-col gap-2">
        <Button
          type="button"
          onClick={onSubmit}
          className="w-full bg-navy text-white hover:bg-steel"
        >
          Login
        </Button>
      </CardFooter>
    </Card>
  );
}