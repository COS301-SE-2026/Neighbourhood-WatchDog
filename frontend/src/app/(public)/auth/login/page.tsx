    "use client";

    import { useState, useEffect } from "react";
    import { useRouter } from "next/navigation";
    import {
    login,
    setSession,
    isAuthenticated,
    verifyMfa,
    logout,
    } from "@/lib/auth/cognito";
    import { fetchMyContext } from "@/lib/api/user-context";
    import { LoginCard } from "@/components/auth-components/login-card";
    import { MfaCard } from "@/components/auth-components/mfa-card";

    export default function LoginPage() {
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [showMfa, setShowMfa] = useState(false);
    const [mfaSession, setMfaSession] = useState("");
    const [mfaDestination, setMfaDestination] = useState("");

    useEffect(() => {
    const redirectIfAuthenticated = async () => {
        if (!isAuthenticated()) return;

        try {
            const context = await fetchMyContext();
            const firstProperty = context.properties[0];

            if (firstProperty) {
                router.replace(
                    `/dashboard/properties/${firstProperty.id}/cameras`
                );
            } else {
                router.replace("/dashboard");
            }
        } catch (error) {
            console.error(
                "Existing session is invalid. Clearing session.",
                error
            );

            // Remove the invalid session
            logout();
        }
    };

    redirectIfAuthenticated();
    }, [router]);

    const redirectToFirstProperty = async () => {
    const context = await fetchMyContext();

    const firstProperty = context.properties[0];

    if (firstProperty) {
        router.push(
            `/dashboard/properties/${firstProperty.id}/cameras`
        );
    } else {
        router.push("/dashboard");
    }
    };

    const handleLogin = async () => {
    setError(null);

    if (!email.trim() || !password.trim()) {
        setError("Please enter both email and password");
        return;
    }

    setIsLoading(true);

    try {
        const result = await login(email.trim(), password);

        if (result.mfaRequired) {
            setMfaSession(result.session ?? "");

            setMfaDestination(
                result.delivery?.destination ?? ""
            );

            setShowMfa(true);
            return;
        }

        setSession({
            accessToken: result.accessToken!,
            idToken: result.idToken!,
            expiresIn: result.expiresIn,
        });

        setPassword("");

        await redirectToFirstProperty();
    } catch (err) {
        const errorMessage =
            err instanceof Error
                ? err.message
                : "Invalid email or password. Please try again.";

        setError(errorMessage);
        console.error("Login error:", err);
    } finally {
        setIsLoading(false);
    }
    };

    const handleMfaVerify = async (code: string) => {
    setError(null);
    setIsLoading(true);

    try {
        const tokens = await verifyMfa(
            email.trim(),
            mfaSession,
            code
        );

        setSession(tokens);

        setPassword("");

        await redirectToFirstProperty();
    } catch (err) {
        const errorMessage =
            err instanceof Error
                ? err.message
                : "Invalid verification code.";

        setError(errorMessage);
    } finally {
        setIsLoading(false);
    }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
        handleLogin();
    }
    };

    return (
    <>
        {!showMfa ? (
            <LoginCard
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                onSubmit={handleLogin}
                onKeyDown={handleKeyDown}
                isLoading={isLoading}
                error={error}
            />
        ) : (
            <MfaCard
                destination={mfaDestination}
                onVerify={handleMfaVerify}
                isLoading={isLoading}
                error={error}
                onBack={() => {
                    setShowMfa(false);
                    setMfaSession("");
                    setError(null);
                }}
            />
        )}
    </>
    );
    }
