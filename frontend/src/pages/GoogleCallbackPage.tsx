import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  useEffect(() => {
    const hash = location.hash.replace(/^#/, "");
    const params = new URLSearchParams(hash);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("optimum_token", token);
      navigate("/", { replace: true });
    } else {
      navigate("/login", { replace: true });
    }
  }, [navigate]);
  return (
    <div className="min-h-screen bg-ink flex items-center justify-center">
      <p className="micro">Completing Google sign-in…</p>
    </div>
  );
}
