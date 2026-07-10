"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await api.post("/auth/login", { email, password });
      login(res.data.access_token, res.data.refresh_token);
      toast.success("Logged in successfully");
      router.push("/");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : "Failed to login";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-zinc-950 p-4">
      <Card className="w-full max-w-md border-zinc-800 bg-zinc-900 text-zinc-100 shadow-2xl">
        <CardHeader className="space-y-3 pb-6 text-center">
          {/* Logo */}
          <div className="flex flex-col items-center gap-1 mb-2">
            <span className="text-4xl font-black tracking-wider text-amber-400 leading-none">AARU</span>
            <span className="text-xs font-semibold tracking-[0.3em] text-zinc-400 uppercase">India</span>
          </div>
          <CardTitle className="text-xl font-bold tracking-tight text-zinc-100">Welcome Back</CardTitle>
          <CardDescription className="text-zinc-400">Enter your credentials to access the platform</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 focus:border-amber-400"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-zinc-300">Password</Label>
                <a href="#" className="text-sm font-medium text-amber-400 hover:text-amber-300">
                  Forgot password?
                </a>
              </div>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-amber-400"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button className="w-full bg-amber-500 hover:bg-amber-400 text-black font-bold" type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Sign In
            </Button>
            <div className="text-center text-sm text-zinc-400">
              Don&apos;t have an account?{" "}
              <a href="/register" className="font-medium text-amber-400 hover:text-amber-300">
                Sign up
              </a>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
