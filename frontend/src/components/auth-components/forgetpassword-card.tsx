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

type ForgotPasswordCardProps = {
  className?: string
}

export function ForgotPasswordCard({ className }: ForgotPasswordCardProps) {
  return (
    <Card className={cn(
      "w-full max-w-md sm:max-w-xl rounded-xl border border-brand-gunmetal/20 bg-brand-depth shadow-lg backdrop-blur",
      className
    )}>
      <CardHeader>
        <CardTitle className="text-[2rem] sm:text-[2rem] font-semibold tracking-tight text-brand-frost">
          Forgot your password?
        </CardTitle>

        <CardDescription className="text-base text-brand-ash">
          Enter your email below and we will send a message to reset your password
        </CardDescription>

        <CardAction>
          <Button
            variant="link"
            className="text-brand-pulse hover:text-brand-ice"
          >
            Login
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent>
        <form>
          <div className="flex flex-col gap-6">
            <div className="grid gap-2">
              <Label htmlFor="email" className="font-medium text-brand-ash">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                required
              />
            </div>
          </div>
        </form>
      </CardContent>

      <CardFooter className="flex-col gap-2">
        <Button
          type="submit"
          className="w-full bg-brand-abyss text-brand-frost hover:bg-brand-slate"
        >
          Send reset link
        </Button>
      </CardFooter>
    </Card>
  )
}