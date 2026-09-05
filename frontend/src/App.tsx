import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./state/AuthContext";
import AppShell from "./components/layout/AppShell";
import SplashScreen from "./components/SplashScreen";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import GoogleCallbackPage from "./pages/GoogleCallbackPage";
import IntegrationsPage from "./pages/IntegrationsPage";
import ContentStudioPage from "./pages/ContentStudioPage";
import DashboardPage from "./pages/DashboardPage";
import SocialHubPage from "./pages/SocialHubPage";
import ProductBuilderPage from "./pages/ProductBuilderPage";
import StrategyStudioPage from "./pages/StrategyStudioPage";
import EngagementPage from "./pages/EngagementPage";
import PerformancePage from "./pages/PerformancePage";
import BillingPage from "./pages/BillingPage";

function Protected() {
  const { user, ready } = useAuth();
  if (!ready) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

export default function App() {
  const [splash, setSplash] = useState(true);
  const [hiding, setHiding] = useState(false);

  useEffect(() => {
    const t1 = window.setTimeout(() => setHiding(true), 1600);
    const t2 = window.setTimeout(() => setSplash(false), 2200);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, []);

  return (
    <AuthProvider>
      {splash && <SplashScreen hiding={hiding} />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/auth/google" element={<GoogleCallbackPage />} />
        <Route element={<Protected />}>
          <Route index element={<DashboardPage />} />
          <Route path="integrations" element={<IntegrationsPage />} />
          <Route path="social-hub" element={<SocialHubPage />} />
          <Route path="product-builder" element={<ProductBuilderPage />} />
          <Route path="content" element={<ContentStudioPage />} />
          <Route path="strategy/:id" element={<StrategyStudioPage />} />
          <Route path="engagement" element={<EngagementPage />} />
          <Route path="performance" element={<PerformancePage />} />
          <Route path="billing" element={<BillingPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
