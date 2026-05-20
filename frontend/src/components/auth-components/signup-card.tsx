import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

type SignupCardProps = {
  className?: string
}

export function SignupCard({ className }: SignupCardProps) {
  return (
    <Card className={cn(
      "w-full max-w-md sm:max-w-xl rounded-3xl border border-[rgba(29,42,94,0.12)] bg-white/95 shadow-[0_20px_60px_rgba(29,42,94,0.14)] backdrop-blur",
      className
    )}>
      <CardHeader>
        <CardTitle className="text-3xl sm:text-4xl font-semibold tracking-tight text-[color:var(--color-navy)]">
          Create your account
        </CardTitle>
        <CardDescription className="text-base text-[color:var(--color-body)]">
          Enter your details below to sign up
        </CardDescription>

        <CardAction>
          <Button
            variant="link"
            className="text-[color:var(--color-sky)] hover:text-[color:var(--color-blue)]"
          >
            Login
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <form>
          <div className="flex flex-col gap-6">

            <div className="grid gap-2">
              <Label htmlFor="name" className="font-medium text-[color:var(--color-body)]">
                Full Name
              </Label>
              <Input id="name" type="text" placeholder="John Doe" required />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="email" className="font-medium text-[color:var(--color-body)]">
                Email
              </Label>
              <Input id="email" type="email" placeholder="m@example.com" required />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password" className="font-medium text-[color:var(--color-body)]">
                Password
              </Label>
              <Input id="password" type="password" required />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="confirmPassword" className="font-medium text-[color:var(--color-body)]">
                Confirm Password
              </Label>
              <Input id="confirmPassword" type="password" required />
            </div>

          </div>
        </form>
      </CardContent>

      <CardFooter className="flex-col gap-2">
        <Button
          type="submit"
          className="w-full bg-[color:var(--color-navy)] text-white hover:bg-[color:var(--color-steel)]"
        >
          Sign Up
        </Button>
      </CardFooter>
    </Card>
  )
}