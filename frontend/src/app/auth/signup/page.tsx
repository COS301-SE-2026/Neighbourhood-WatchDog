"use client";

import { SignupCard } from "../../../components/auth-components/signup-card";

export default function Page() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSignUp = async () => {
    try {
      // basic safety check 
      if (password !== confirmPassword) {
        alert("Passwords do not match");
        return;
      }

      await signUp(email, password, name, address);

      router.push("/auth/login");
    } catch (err) {
      console.error("Signup failed:", err);
    }
  };

  return (
    <SignupCard />
  );
}