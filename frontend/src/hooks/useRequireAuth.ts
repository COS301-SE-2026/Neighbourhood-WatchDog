"use client";

import { useEffect} from "react"; //use state
import { useRouter } from "next/navigation";

export function useRequireAuth() {
    const router = useRouter();
    // const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem("accessToken");

        if (!token) {
            router.replace("/auth/login");
            return;
        }

        // TODO: Send token to backend for JWT validation
        // setLoading(false);
    }, [router]);

    // return { loading };
}