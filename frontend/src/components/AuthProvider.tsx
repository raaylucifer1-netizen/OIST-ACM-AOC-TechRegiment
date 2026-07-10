"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Loader2 } from "lucide-react";

const publicRoutes = ["/login", "/register", "/verify-email"];

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, fetchUser } = useAuthStore();
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
    if (!isLoading && mounted) {
      const isPublicRoute = publicRoutes.includes(pathname);
      if (!isAuthenticated && !isPublicRoute) {
        router.push("/login");
      } else if (isAuthenticated && isPublicRoute) {
        router.push("/");
      }
    }
  }, [isLoading, isAuthenticated, pathname, router, mounted]);

  const hasToken = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  if (!mounted) {
    return <>{children}</>;
  }

  if (isLoading && hasToken) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
      </div>
    );
  }

  return <>{children}</>;
}
