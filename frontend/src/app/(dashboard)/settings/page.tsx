"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  User,
  Shield,
  Database,
  Cpu,
  Bell,
  Loader2,
  Save,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import { toast } from "sonner";

const TABS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "security", label: "Security", icon: Shield },
  { id: "system", label: "System", icon: Cpu },
  { id: "database", label: "Database", icon: Database },
];

export default function SettingsPage() {
  const { user, fetchUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState("profile");
  const [profile, setProfile] = useState<any>(null);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  // Profile form
  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [company, setCompany] = useState("");
  const [country, setCountry] = useState("");

  // Password form
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showOldPw, setShowOldPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [savingPw, setSavingPw] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchSystem();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoadingProfile(true);
      const res = await api.get("/settings/profile");
      setProfile(res.data);
      setFullName(res.data.full_name || "");
      setBio(res.data.bio || "");
      setCompany(res.data.company || "");
      setCountry(res.data.country || "");
    } catch {
      toast.error("Failed to load profile");
    } finally {
      setLoadingProfile(false);
    }
  };

  const fetchSystem = async () => {
    try {
      const res = await api.get("/settings/system-info");
      setSystemInfo(res.data);
    } catch {}
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSavingProfile(true);
      await api.patch("/settings/profile", {
        full_name: fullName.trim(),
        bio: bio.trim() || null,
        company: company.trim() || null,
        country: country.trim() || null,
      });
      await fetchUser();
      toast.success("Profile updated successfully");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirmPw) {
      toast.error("New passwords do not match");
      return;
    }
    if (newPw.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    try {
      setSavingPw(true);
      await api.post("/auth/change-password", {
        old_password: oldPw,
        new_password: newPw,
      });
      toast.success("Password changed successfully");
      setOldPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to change password");
    } finally {
      setSavingPw(false);
    }
  };

  if (loadingProfile) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your account, security, and platform configuration.</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar tabs */}
        <nav className="w-48 shrink-0 space-y-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors text-left ${
                activeTab === tab.id
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-white"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 space-y-6">
          {/* Profile Tab */}
          {activeTab === "profile" && (
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your public profile and account details.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSaveProfile} className="space-y-5">
                  <div className="flex items-center gap-4 pb-4 border-b">
                    <div className="h-16 w-16 rounded-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center text-2xl font-bold">
                      {fullName?.split(" ").map((n: string) => n[0]).join("").toUpperCase().substring(0, 2) || "U"}
                    </div>
                    <div>
                      <p className="font-semibold">{fullName || "Your Name"}</p>
                      <p className="text-sm text-muted-foreground">{profile?.email}</p>
                      <Badge variant="outline" className="text-xs mt-1 capitalize">{profile?.role}</Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" value={profile?.email || ""} disabled className="opacity-60" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="company">Company / Organization</Label>
                      <Input
                        id="company"
                        placeholder="e.g. Acme Corp"
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="country">Country</Label>
                      <Input
                        id="country"
                        placeholder="e.g. India"
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      placeholder="Tell us a little about yourself or your research goals..."
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      rows={3}
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button type="submit" disabled={savingProfile} className="gap-2">
                      {savingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                      Save Profile
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Security Tab */}
          {activeTab === "security" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Change Password</CardTitle>
                  <CardDescription>Choose a strong password with at least 8 characters.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleChangePassword} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="oldPw">Current Password</Label>
                      <div className="relative">
                        <Input
                          id="oldPw"
                          type={showOldPw ? "text" : "password"}
                          value={oldPw}
                          onChange={(e) => setOldPw(e.target.value)}
                          className="pr-10"
                        />
                        <button
                          type="button"
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                          onClick={() => setShowOldPw(!showOldPw)}
                        >
                          {showOldPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="newPw">New Password</Label>
                      <div className="relative">
                        <Input
                          id="newPw"
                          type={showNewPw ? "text" : "password"}
                          value={newPw}
                          onChange={(e) => setNewPw(e.target.value)}
                          className="pr-10"
                        />
                        <button
                          type="button"
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                          onClick={() => setShowNewPw(!showNewPw)}
                        >
                          {showNewPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirmPw">Confirm New Password</Label>
                      <Input
                        id="confirmPw"
                        type="password"
                        value={confirmPw}
                        onChange={(e) => setConfirmPw(e.target.value)}
                      />
                      {confirmPw && newPw !== confirmPw && (
                        <p className="text-xs text-red-500 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> Passwords do not match
                        </p>
                      )}
                      {confirmPw && newPw === confirmPw && newPw.length >= 8 && (
                        <p className="text-xs text-green-600 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Passwords match
                        </p>
                      )}
                    </div>
                    <div className="flex justify-end pt-2">
                      <Button
                        type="submit"
                        disabled={savingPw || !oldPw || !newPw || !confirmPw || newPw !== confirmPw}
                      >
                        {savingPw && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Change Password
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Account Status</CardTitle>
                  <CardDescription>Your account verification and security status.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between py-2 border-b">
                    <div>
                      <p className="text-sm font-medium">Email Verification</p>
                      <p className="text-xs text-muted-foreground">{profile?.email}</p>
                    </div>
                    <Badge variant={profile?.is_verified ? "default" : "destructive"}>
                      {profile?.is_verified ? "Verified" : "Unverified"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <p className="text-sm font-medium">Account Role</p>
                      <p className="text-xs text-muted-foreground">Your permission level on this platform</p>
                    </div>
                    <Badge variant="outline" className="capitalize">{profile?.role}</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* System Tab */}
          {activeTab === "system" && (
            <Card>
              <CardHeader>
                <CardTitle>System Information</CardTitle>
                <CardDescription>Platform configuration and runtime details.</CardDescription>
              </CardHeader>
              <CardContent>
                {systemInfo ? (
                  <div className="space-y-3">
                    {[
                      { label: "App Name", value: systemInfo.app_name },
                      { label: "Version", value: systemInfo.app_version },
                      { label: "AI Model", value: systemInfo.gemini_model },
                      { label: "Database Type", value: systemInfo.database_type },
                      { label: "Database Size", value: `${systemInfo.database_size_mb} MB` },
                      { label: "Email Mode", value: systemInfo.email_mode },
                      { label: "Debug Mode", value: systemInfo.debug_mode ? "Enabled" : "Disabled" },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex items-center justify-between py-2 border-b last:border-0">
                        <span className="text-sm text-muted-foreground">{label}</span>
                        <span className="text-sm font-medium font-mono">{value}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Database Tab */}
          {activeTab === "database" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Database Overview</CardTitle>
                  <CardDescription>Information about your persona database and storage.</CardDescription>
                </CardHeader>
                <CardContent>
                  {systemInfo ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-sm text-muted-foreground">Database Engine</span>
                        <span className="text-sm font-medium">{systemInfo.database_type}</span>
                      </div>
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="text-sm text-muted-foreground">Database Size</span>
                        <span className="text-sm font-medium">{systemInfo.database_size_mb} MB</span>
                      </div>
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-muted-foreground">Status</span>
                        <Badge variant="default" className="bg-green-600">Connected</Badge>
                      </div>
                    </div>
                  ) : (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  )}
                </CardContent>
              </Card>

              <Card className="border-red-200 dark:border-red-900">
                <CardHeader>
                  <CardTitle className="text-red-600">Danger Zone</CardTitle>
                  <CardDescription>
                    These actions are irreversible. Proceed with extreme caution.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20">
                    <div>
                      <p className="text-sm font-medium">Delete All Personas</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Permanently remove all imported personas from your account.
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={async () => {
                        if (
                          confirm(
                            "Are you absolutely sure? This will delete ALL your personas and cannot be undone."
                          )
                        ) {
                          try {
                            await api.delete("/personas/bulk/all");
                            toast.success("All personas deleted");
                          } catch {
                            toast.error("Failed to delete personas");
                          }
                        }
                      }}
                    >
                      Delete All Personas
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
