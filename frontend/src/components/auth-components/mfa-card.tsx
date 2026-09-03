"use client";

import { useState, useRef } from "react";

import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";

import { Loader2, ArrowLeft } from "lucide-react";

import { cn } from "@/lib/utils";


type MfaCardProps = {
  className?: string;

  destination: string;

  onVerify: (code: string) => void;

  onBack?: () => void;

  isLoading?: boolean;

  error?: string | null;
};


export function MfaCard({
  className,
  destination,
  onVerify,
  onBack,
  isLoading = false,
  error = null,
}: MfaCardProps) {

  const [code, setCode] = useState(
    ["", "", "", "", "", ""]
  );

  const inputs = useRef<(HTMLInputElement | null)[]>([]);


  const handleChange = (
    value: string,
    index: number
  ) => {

    // Only allow numbers
    if (!/^\d?$/.test(value)) return;


    const newCode = [...code];

    newCode[index] = value;

    setCode(newCode);


    // Move to next box
    if (
      value &&
      index < 5
    ) {
      inputs.current[index + 1]?.focus();
    }
  };


  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    index: number
  ) => {

    if (
      e.key === "Backspace" &&
      !code[index] &&
      index > 0
    ) {
      inputs.current[index - 1]?.focus();
    }

  };


  const handleSubmit = () => {
    const otp = code.join("");

    if (otp.length !== 6) return;

    onVerify(otp);
  };


  return (
    <Card
      className={cn(
        "w-full max-w-lg sm:max-w-2xl rounded-xl border border-brand-gunmetal/20 bg-brand-depth shadow-lg backdrop-blur",
        className
      )}
    >

      <CardHeader>

        <CardTitle className="
          text-[2rem]
          font-semibold
          tracking-tight
          text-brand-frost
        ">
          Verify your email
        </CardTitle>


        <CardDescription className="text-base text-brand-ash">
          Enter the 6-digit code sent to{" "}
          <span className="font-medium text-brand-frost">
            {destination}
          </span>
        </CardDescription>

      </CardHeader>



      <CardContent>

        <div className="flex flex-col gap-6">


          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                {error}
              </AlertDescription>
            </Alert>
          )}



          <div className="flex justify-center gap-3">

            {code.map((digit, index) => (

              <Input
                key={index}

                ref={(el) => {
                  inputs.current[index] = el;
                }}

                value={digit}

                onChange={(e) =>
                  handleChange(
                    e.target.value,
                    index
                  )
                }

                onKeyDown={(e) =>
                  handleKeyDown(
                    e,
                    index
                  )
                }

                maxLength={1}

                disabled={isLoading}

                className="
                  h-14
                  w-12
                  text-center
                  text-xl
                  font-semibold
                "

                inputMode="numeric"

              />

            ))}

          </div>


        </div>

      </CardContent>



      <CardFooter className="flex-col gap-3">


        <Button
          type="button"
          onClick={handleSubmit}
          disabled={
            isLoading ||
            code.join("").length !== 6
          }

          className="
            w-full
            bg-brand-abyss
            text-brand-frost
            hover:bg-brand-slate
          "
        >

          {isLoading ? (

            <>
              <Loader2
                className="
                  mr-2
                  h-4
                  w-4
                  animate-spin
                "
              />

              Verifying...

            </>

          ) : (

            "Verify Code"

          )}

        </Button>



        {onBack && (

          <Button
            variant="ghost"
            onClick={onBack}
            disabled={isLoading}
            className="text-brand-ash"
          >

            <ArrowLeft className="mr-2 h-4 w-4"/>

            Back to login

          </Button>

        )}


      </CardFooter>

    </Card>
  );
}