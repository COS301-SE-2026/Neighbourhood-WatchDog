"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { LoginCard } from "@/components/auth-components/login-card";
import { SignupCard } from "@/components/auth-components/signup-card";
import { ConfirmCard } from "@/components/auth-components/confirm-card";

export default function CardsSection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Cards</h2>

      {/* Default card */}
      <Card>
        <CardHeader>
          <CardTitle>Default Card</CardTitle>
        </CardHeader>
        <CardContent>
          Base shadcn styling
        </CardContent>
      </Card>

      {/* Login card */}
      <LoginCard
        email="john@example.com"
        setEmail={() => {}}
        password="password123"
        setPassword={() => {}}
        onSubmit={() => {}}
        onKeyDown={() => {}}
        isLoading={false}
        error={null}
      />

      <SignupCard
        firstName= "Name"
        setFirstName={() => {}}
        lastName={"Surname"}
        setLastName={() => {}}
        email={"email@email.com"}
        setEmail={() => {}}
        password={"Password"}
        setPassword={() => {}}
        confirmPassword={"Password"}
        setConfirmPassword={() => {}}
        address={"Dummy Address"}
        setAddress={() => {}}
        onSubmit={() => {}}
        onKeyDown={() => {}}
        isLoading={false}
        error={null}
      />

      <ConfirmCard
        email={"email@email.com"}
        setEmail={() => {}}
        code={"676767"}
        setCode={() => {}}
        onSubmit={() => {}}
        onResendCode={() => {}}
        onKeyDown={() => {}}
        isLoading={false}
        isResending={false}
        error={null}
        success={false}
        resendSuccess={false}
      />


    </section>
  );
}