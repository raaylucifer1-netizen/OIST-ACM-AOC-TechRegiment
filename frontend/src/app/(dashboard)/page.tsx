"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/authStore";
import { Users, BarChart2, MessageSquare, Activity, Loader2, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#f43f5e", "#0ea5e9", "#a855f7"];

export default function Dashboard() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/analytics/dashboard")
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { title: "Total Personas", value: data?.total_personas?.toLocaleString() ?? "0", icon: Users, color: "text-blue-500", href: "/personas" },
    { title: "Simulations Run", value: data?.total_simulations?.toLocaleString() ?? "0", icon: BarChart2, color: "text-purple-500", href: "/simulations" },
    { title: "Completed", value: data?.completed_simulations?.toLocaleString() ?? "0", icon: Activity, color: "text-green-500", href: "/simulations" },
    { title: "Conversations", value: data?.total_conversations?.toLocaleString() ?? "0", icon: MessageSquare, color: "text-orange-500", href: "/conversations" },
  ];

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
      </div>
    );
  }

  const charts = data?.charts || {};
  const hasPersonas = (data?.total_personas || 0) > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Welcome back, {user?.full_name?.split(" ")[0] || "User"}
        </h2>
        <p className="text-muted-foreground">
          {hasPersonas
            ? `You have ${data.total_personas.toLocaleString()} personas ready for simulation.`
            : "Import personas to start running simulations."}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card
            key={stat.title}
            className="cursor-pointer hover:border-zinc-400 transition-colors"
            onClick={() => router.push(stat.href)}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {hasPersonas ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Gender distribution */}
          {charts.gender_distribution?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Gender Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie data={charts.gender_distribution} dataKey="value" cx="50%" cy="50%" outerRadius={65}
                      label={({ name, percent }: any) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                      {charts.gender_distribution.map((_: any, i: number) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Age distribution */}
          {charts.age_distribution?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Age Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={charts.age_distribution}>
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Top states */}
          {charts.top_states?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Top States</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={charts.top_states} layout="vertical" margin={{ left: 10 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8b5cf6" radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card className="border-2 border-dashed border-zinc-200 dark:border-zinc-800">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-12 w-12 text-zinc-300 mb-4" />
            <h3 className="font-semibold text-lg mb-2">No personas yet</h3>
            <p className="text-muted-foreground text-sm mb-5 max-w-sm">
              Import your persona database to unlock simulations, conversations, and analytics.
            </p>
            <button
              onClick={() => router.push("/personas")}
              className="flex items-center gap-2 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 px-4 py-2 text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Import Personas <ArrowRight className="h-4 w-4" />
            </button>
          </CardContent>
        </Card>
      )}

      {/* Recent simulations */}
      {data?.recent_simulations?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Simulations</CardTitle>
            <CardDescription>Your latest simulation runs.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.recent_simulations.map((sim: any) => (
                <div
                  key={sim.id}
                  className="flex items-center gap-4 rounded-lg border p-3 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors"
                  onClick={() => router.push("/simulations")}
                >
                  <div className="h-9 w-9 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0">
                    <Activity className="h-4 w-4 text-zinc-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{sim.title}</p>
                    <p className="text-xs text-muted-foreground capitalize">{sim.type} · {sim.sample_size} personas</p>
                  </div>
                  <span className={`text-xs font-medium capitalize px-2 py-0.5 rounded-full ${
                    sim.status === "completed" ? "bg-green-100 text-green-700" :
                    sim.status === "failed" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"
                  }`}>
                    {sim.status}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
