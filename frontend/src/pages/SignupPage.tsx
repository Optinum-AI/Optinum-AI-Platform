import { Link } from "react-router-dom";
import { User } from "lucide-react";
import { AuthLayout, AuthCard } from "./LoginPage";
import { useAuth } from "../state/AuthContext";
import { useState } from "react";

export default function SignupPage() {
  const { signup } = useAuth();
  const [name, setName] = useState("");
  return (
    <AuthLayout>
      <AuthCard
        title="Request Access"
        submitLabel="Provision Account"
        onSubmit={(email, password) => signup(email, password, name)}
        extra={
          <div className="relative">
            <User size={15} className="absolute left-1 top-1/2 -translate-y-1/2 text-salmon/60" />
            <input className="input pl-8" required placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
        }
        footer={<>Already provisioned? <Link to="/login" className="text-accent2 font-semibold hover:underline">Initialize Session</Link></>}
      />
    </AuthLayout>
  );
}
