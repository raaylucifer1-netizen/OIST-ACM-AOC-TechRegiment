"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const authRoutes = ["/login", "/register", "/verify-email"];

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchUser } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Only fetch user on initial load if we have a token
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token && !isAuthenticated) {
      fetchUser();
    }
  }, [fetchUser, isAuthenticated]);

  useEffect(() => {
    if (mounted) {
      const isAuthRoute = authRoutes.includes(pathname);
      // Redirect authenticated users away from login/register pages
      if (isAuthenticated && isAuthRoute) {
        router.push("/dashboard");
      }
    }
  }, [isAuthenticated, pathname, router, mounted]);

  // AuthProvider no longer renders loaders or blocks rendering.
  // It simply initializes auth state. Route protection is handled by AuthGuard.
  return <>{children}</>;
}
