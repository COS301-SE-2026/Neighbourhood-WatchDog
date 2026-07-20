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
import { Alert, AlertDescription } from "@/components/ui/alert"; 
import { Loader2 } from "lucide-react"; 

type LoginCardProps = {
  className?: string;

  email: string;
  setEmail: (v: string) => void;

  password: string;
  setPassword: (v: string) => void;

  onSubmit: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void; //Enter key
  
  isLoading?: boolean; //loading state
  error?: string | null;
};

export function LoginCard({
  className,
  email,
  setEmail,
  password,
  setPassword,
  onSubmit,
  onKeyDown,
  isLoading = false,
  error = null,
}: LoginCardProps) {
  return (
    <Card
      className={cn(
        "w-full max-w-md sm:max-w-xl rounded-xl shadow-lg backdrop-blur",
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
          <Button variant="link" asChild>
            <a href="/auth/signup">Sign Up</a>
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col gap-6">
          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="mb-2">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* EMAIL */}
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="m@example.com"
              disabled={isLoading} // Disable during loading
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
              onKeyDown={onKeyDown} //Pass key handler
              disabled={isLoading} //Disable during loading
              required
            />
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex-col gap-2">
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isLoading} //Disable during loading
          className="w-full bg-navy text-white hover:bg-steel"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Logging in...
            </>
          ) : (
            "Login"
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}