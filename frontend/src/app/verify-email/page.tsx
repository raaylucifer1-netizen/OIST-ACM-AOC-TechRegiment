"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";

function VerifyEmailContent() {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Verifying your email...");
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("Verification token is missing.");
      return;
    }

    const verifyToken = async () => {
      try {
        await api.post("/auth/verify-email", { token });
        setStatus("success");
        setMessage("Email verified successfully! You can now log in.");
        toast.success("Email verified successfully!");
      } catch (err: any) {
        setStatus("error");
        const detail = err.response?.data?.detail;
        setMessage(typeof detail === "string" ? detail : "Failed to verify email. The token might be invalid or expired.");
      }
    };

    verifyToken();
  }, [searchParams]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-4">
            {status === "loading" && <Loader2 className="h-12 w-12 animate-spin text-blue-500" />}
            {status === "success" && <CheckCircle2 className="h-12 w-12 text-green-500" />}
            {status === "error" && <XCircle className="h-12 w-12 text-red-500" />}
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">Email Verification</CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Content area if needed */}
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          {status !== "loading" && (
            <Button className="w-full" onClick={() => router.push("/login")}>
              Go to Login
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex h-screen w-full items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
