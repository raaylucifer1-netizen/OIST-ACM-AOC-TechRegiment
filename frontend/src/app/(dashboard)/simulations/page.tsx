"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Loader2, Play, BrainCircuit, BarChart2, PieChart, FileText,
  TrendingUp, Users, ThumbsUp, ThumbsDown, Minus, CheckCircle2, Plus, ChevronDown,
} from "lucide-react";
import {
  PieChart as RechartsPie, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const SIM_TYPES = [
  { value: "market", label: "Market Research" },
  { value: "product_launch", label: "Product Launch" },
  { value: "pricing", label: "Pricing Test" },
  { value: "feature_test", label: "Feature Test" },
  { value: "ad_test", label: "Ad Test" },
  { value: "brand", label: "Brand Perception" },
  { value: "election", label: "Election Poll" },
  { value: "policy", label: "Policy Survey" },
  { value: "crisis", label: "Crisis Response" },
  { value: "interview", label: "Consumer Interview" },
];

const SENTIMENT_COLORS = { Positive: "#22c55e", Neutral: "#94a3b8", Negative: "#ef4444" };
const CHART_COLORS = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#f43f5e", "#0ea5e9"];

export default function SimulationsPage() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [pastSimulations, setPastSimulations] = useState<any[]>([]);
  const [selectedSimId, setSelectedSimId] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [analyticsCharts, setAnalyticsCharts] = useState<any>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [activeResultTab, setActiveResultTab] = useState("responses");

  const [form, setForm] = useState({
    title: "New Simulation",
    type: "market",
    prompt: "Would you buy a ₹15,000 AI smartwatch with health tracking features?",
    sample_size: 10,
    city: "__all__",
    age_min: "",
    age_max: "",
    income_min: "",
    income_max: "",
  });

  useEffect(() => { fetchPastSimulations(); }, []);

  const fetchPastSimulations = async (selectId?: string) => {
    try {
      const res = await api.get("/simulations");
      const sims = res.data.simulations || [];
      setPastSimulations(sims);
      if (selectId) {
        setSelectedSimId(selectId);
        loadSimulation(selectId);
      } else if (sims.length > 0 && !selectedSimId) {
        setSelectedSimId(sims[0].id);
        loadSimulation(sims[0].id);
      }
    } catch {}
  };

  const loadSimulation = async (simId: string) => {
    try {
      setLoading(true);
      setResults([]);
      setAnalytics(null);
      setAnalyticsCharts(null);
      setReport(null);
      const [detailRes, analyticsRes] = await Promise.all([
        api.get(`/simulations/${simId}`),
        api.get(`/analytics/simulations/${simId}/analytics`),
      ]);
      const sim = detailRes.data.simulation;
      setForm((f) => ({ ...f, title: sim.title, type: sim.type, prompt: sim.question, sample_size: sim.sample_size }));
      const formatted = detailRes.data.responses.map((r: any) => ({
        persona_id: r.persona_id,
        persona_label: r.persona_label,
        response: r.response,
        confidence: r.confidence,
        decision: r.decision,
        sentiment: r.sentiment,
      }));
      setResults(formatted);
      setAnalytics(analyticsRes.data.analytics);
      setAnalyticsCharts(analyticsRes.data.charts);
    } catch {} finally { setLoading(false); }
  };

  const resetForm = () => {
    setSelectedSimId(null);
    setResults([]);
    setAnalytics(null);
    setAnalyticsCharts(null);
    setReport(null);
    setForm({ title: "New Simulation", type: "market", prompt: "", sample_size: 10, city: "__all__", age_min: "", age_max: "", income_min: "", income_max: "" });
  };

  const runSimulation = async () => {
    if (!form.prompt.trim()) { toast.error("Please enter a scenario prompt"); return; }
    try {
      setLoading(true);
      setResults([]);
      setAnalytics(null);
      setAnalyticsCharts(null);
      setReport(null);
      setSelectedSimId(null);
      setActiveResultTab("responses");

      const config: any = {};
      if (form.city !== "__all__") config.city = form.city;
      if (form.age_min) config.age_min = parseInt(form.age_min);
      if (form.age_max) config.age_max = parseInt(form.age_max);
      if (form.income_min) config.income_min = parseInt(form.income_min);
      if (form.income_max) config.income_max = parseInt(form.income_max);

      const payload = { type: form.type, title: form.title, question: form.prompt, sample_size: form.sample_size, config };
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
      const response = await fetch(`${API_URL}/simulations/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });

      if (!response.ok) { toast.error("Simulation failed to start"); return; }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      if (!reader) return;
      let simId: string | undefined;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const dataStr = line.slice(6).trim();
          if (!dataStr) continue;
          try {
            const data = JSON.parse(dataStr);
            if (data.simulation_id) { simId = data.simulation_id; }
            else if (data.persona_id) {
              setResults((prev) => [...prev, { persona_id: data.persona_id, persona_label: data.persona_label, response: data.response, confidence: data.confidence, decision: data.decision }]);
            } else if (data.analytics) {
              setAnalytics(data.analytics);
            } else if (data.error) { toast.error(data.error); }
          } catch {}
        }
      }
      toast.success("Simulation complete");
      if (simId) {
        setSelectedSimId(simId);
        try {
          const analyticsRes = await api.get(`/analytics/simulations/${simId}/analytics`);
          setAnalyticsCharts(analyticsRes.data.charts);
          if (!analytics) setAnalytics(analyticsRes.data.analytics);
        } catch {}
        await fetchPastSimulations(simId);
      }
    } catch (e: any) { toast.error(e.message || "Simulation failed"); }
    finally { setLoading(false); }
  };

  const generateReport = async () => {
    if (!selectedSimId) return;
    try {
      setGeneratingReport(true);
      const res = await api.post(`/reports/generate/${selectedSimId}`);
      setReport(res.data.content);
      setActiveResultTab("report");
      toast.success("Report generated");
    } catch { toast.error("Failed to generate report"); }
    finally { setGeneratingReport(false); }
  };

  const decisionLabel = (d: string) => {
    if (!d) return null;
    const map: Record<string, string> = {
      yes: "✅ Will Buy", no: "❌ Won't Buy", maybe: "🤔 Maybe",
      stay: "✅ Will Stay", leave: "❌ Will Leave", consider: "🤔 Considering",
      persuaded: "✅ Persuaded", not_persuaded: "❌ Not Persuaded", neutral: "➖ Neutral",
      support: "✅ Supports", oppose: "❌ Opposes", option_a: "🅰 Chose A", option_b: "🅱 Chose B",
      high: "🟢 High Trust", medium: "🟡 Medium Trust", low: "🔴 Low Trust",
    };
    return map[d.toLowerCase()] || d;
  };

  const decisionBg = (d: string) => {
    if (!d) return "bg-zinc-100 text-zinc-600 border-zinc-200";
    const d2 = d.toLowerCase();
    if (["yes","stay","persuaded","support","option_a","high"].includes(d2)) return "bg-green-50 text-green-700 border-green-200";
    if (["no","leave","not_persuaded","oppose","low"].includes(d2)) return "bg-red-50 text-red-700 border-red-200";
    return "bg-amber-50 text-amber-700 border-amber-200";
  };

  const sentimentBar = (s: number | null | undefined) => {
    if (s == null) return null;
    const pct = Math.round(((s + 1) / 2) * 100);
    const color = s > 0.2 ? "bg-green-400" : s < -0.2 ? "bg-red-400" : "bg-zinc-400";
    return { pct, color };
  };

  const positiveRate = analytics?.positive_rate ?? null;
  const avgConfidence = analytics?.avg_confidence ?? null;
  const totalResponses = analytics?.total_responses ?? results.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Simulations</h2>
          <p className="text-muted-foreground">Run multi-persona scenario simulations and analyze the results.</p>
        </div>
        {selectedSimId && (
          <Button variant="outline" size="sm" onClick={resetForm} className="gap-2">
            <Plus className="h-4 w-4" /> New Simulation
          </Button>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: Form */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Simulation Setup</CardTitle>
              <CardDescription>Describe a scenario — our AI will ask real personas and collect their honest opinions.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {pastSimulations.length > 0 && (
                <div className="space-y-1.5 pb-3 border-b">
                  <Label className="text-xs">Load Past Simulation</Label>
                  <Select value={selectedSimId || "__new__"} onValueChange={(v: string | null) => { if (!v || v === "__new__") resetForm(); else { setSelectedSimId(v); loadSimulation(v); } }}>
                    <SelectTrigger className="h-9"><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__new__">+ New Simulation</SelectItem>
                      {pastSimulations.map((s: any) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.title} ({new Date(s.created_at).toLocaleDateString()})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="space-y-1.5">
                <Label className="text-xs">Title</Label>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="h-9" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Simulation Type</Label>
                <Select value={form.type} onValueChange={(v: string | null) => v && setForm({ ...form, type: v })}>
                  <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>{SIM_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">What do you want to ask? <span className="text-muted-foreground">(your scenario)</span></Label>
                <Textarea value={form.prompt} onChange={(e) => setForm({ ...form, prompt: e.target.value })} rows={4} placeholder="e.g. Would you buy a ₹15,000 AI smartwatch with health tracking? Or: What do you think of Jio's new unlimited plan?" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Sample Size (max 50)</Label>
                <Input type="number" min={1} max={50} value={form.sample_size} onChange={(e) => setForm({ ...form, sample_size: Math.min(50, Math.max(1, parseInt(e.target.value) || 1)) })} className="h-9" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Filter: City</Label>
                <Select value={form.city} onValueChange={(v: string | null) => v && setForm({ ...form, city: v })}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="All cities" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All Cities</SelectItem>
                    {["Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Kolkata","Pune","Ahmedabad","Jaipur","Surat","Lucknow","Bhopal","Indore","Kochi"].map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <Label className="text-xs">Age Min</Label>
                  <Input type="number" className="h-9" placeholder="18" value={form.age_min} onChange={(e) => setForm({ ...form, age_min: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Age Max</Label>
                  <Input type="number" className="h-9" placeholder="65" value={form.age_max} onChange={(e) => setForm({ ...form, age_max: e.target.value })} />
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t pt-4">
              <Button onClick={runSimulation} disabled={loading} className="w-full gap-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {loading ? "Running..." : "Run Simulation"}
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Right: Results */}
        <div className="lg:col-span-3 space-y-4">
          {/* Summary metrics */}
          {analytics && (
            <div className="grid grid-cols-3 gap-3">
              <Card className="p-3">
                <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Users className="h-3.5 w-3.5" />Responses</p>
                <p className="text-2xl font-bold">{totalResponses}</p>
              </Card>
              <Card className="p-3">
                <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><ThumbsUp className="h-3.5 w-3.5" />Acceptance</p>
                <p className={`text-2xl font-bold ${positiveRate >= 60 ? "text-green-600" : positiveRate >= 40 ? "text-yellow-600" : "text-red-600"}`}>{positiveRate}%</p>
              </Card>
              <Card className="p-3">
                <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><TrendingUp className="h-3.5 w-3.5" />Avg Confidence</p>
                <p className="text-2xl font-bold">{avgConfidence != null ? `${(avgConfidence * 100).toFixed(0)}%` : "—"}</p>
              </Card>
            </div>
          )}

          <Card className="flex flex-col">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <Tabs value={activeResultTab} onValueChange={setActiveResultTab} className="w-auto">
                  <TabsList>
                    <TabsTrigger value="responses" className="gap-1.5 text-xs"><BrainCircuit className="h-3.5 w-3.5" />Responses</TabsTrigger>
                    <TabsTrigger value="analytics" className="gap-1.5 text-xs" disabled={!analytics}><BarChart2 className="h-3.5 w-3.5" />Analytics</TabsTrigger>
                    <TabsTrigger value="report" className="gap-1.5 text-xs" disabled={!selectedSimId}><FileText className="h-3.5 w-3.5" />Report</TabsTrigger>
                  </TabsList>
                </Tabs>
                {selectedSimId && (
                  <Button size="sm" variant="outline" className="gap-1.5 text-xs h-8" onClick={generateReport} disabled={generatingReport}>
                    {generatingReport ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
                    Generate Report
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="flex-1">
              {/* Responses tab */}
              {activeResultTab === "responses" && (
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                  {results.length === 0 && !loading && (
                    <div className="flex flex-col items-center justify-center h-56 text-center text-muted-foreground border-2 border-dashed rounded-xl">
                      <BrainCircuit className="h-10 w-10 mb-3 text-zinc-300" />
                      <p className="text-sm font-medium">No responses yet</p>
                      <p className="text-xs mt-1 text-zinc-400">Set up your scenario on the left and click Run Simulation</p>
                    </div>
                  )}
                  {results.map((r, i) => {
                    const sb = sentimentBar(r.sentiment);
                    const label = r.persona_label || r.persona_id || "Persona";
                    // Parse label: "P00001 (28M, Mumbai)"
                    const match = label.match(/^(\w+)\s*\((.+)\)$/);
                    const pid = match ? match[1] : label;
                    const demo = match ? match[2] : "";
                    return (
                      <div key={i} className="rounded-xl border bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
                        {/* Persona header strip */}
                        <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800 border-b">
                          <div className="flex items-center gap-2.5">
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                              {pid.replace("P","").padStart(2,"0").slice(-2)}
                            </div>
                            <div>
                              <p className="text-sm font-semibold leading-tight">{pid}</p>
                              {demo && <p className="text-[11px] text-muted-foreground">{demo}</p>}
                            </div>
                          </div>
                          {r.decision && (
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${decisionBg(r.decision)}`}>
                              {decisionLabel(r.decision)}
                            </span>
                          )}
                        </div>
                        {/* Response text */}
                        <div className="px-4 py-3">
                          <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">{r.response}</p>
                        </div>
                        {/* Footer: sentiment + confidence */}
                        <div className="flex items-center gap-4 px-4 py-2 border-t bg-zinc-50/50 dark:bg-zinc-800/50">
                          {sb && (
                            <div className="flex items-center gap-2 flex-1">
                              <span className="text-[11px] text-muted-foreground w-14">Sentiment</span>
                              <div className="flex-1 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${sb.color}`} style={{ width: `${sb.pct}%` }} />
                              </div>
                              <span className="text-[11px] text-muted-foreground w-10 text-right">
                                {sb.pct > 55 ? "Positive" : sb.pct < 45 ? "Negative" : "Neutral"}
                              </span>
                            </div>
                          )}
                          {r.confidence != null && (
                            <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                              {(r.confidence * 100).toFixed(0)}% confident
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {loading && (
                    <div className="flex items-center gap-3 text-sm text-muted-foreground border rounded-xl p-4 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500 shrink-0" />
                      <div>
                        <p className="font-medium text-blue-700 dark:text-blue-300">Personas are responding...</p>
                        <p className="text-xs text-blue-500 mt-0.5">Each person is thinking through your question based on their profile</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Analytics tab */}
              {activeResultTab === "analytics" && analytics && (
                <div className="space-y-6">
                  {/* Sentiment pie + Decision bar */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Sentiment</p>
                      <ResponsiveContainer width="100%" height={160}>
                        <RechartsPie>
                          <Pie data={analyticsCharts?.sentiment || []} dataKey="value" cx="50%" cy="50%" outerRadius={60} label={({ name, percent }: any) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                            {(analyticsCharts?.sentiment || []).map((entry: any, i: number) => (
                              <Cell key={i} fill={entry.color || CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </RechartsPie>
                      </ResponsiveContainer>
                    </div>
                    <div>
                      <p className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Decisions</p>
                      <ResponsiveContainer width="100%" height={160}>
                        <BarChart data={analyticsCharts?.decisions || []} layout="vertical" margin={{ left: 10, right: 10 }}>
                          <XAxis type="number" hide />
                          <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {(analyticsCharts?.decisions || []).map((_: any, i: number) => (
                              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  {/* Age distribution */}
                  {analyticsCharts?.age_groups?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Age Groups</p>
                      <ResponsiveContainer width="100%" height={140}>
                        <BarChart data={analyticsCharts.age_groups}>
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                  {/* Gender + Income */}
                  <div className="grid grid-cols-2 gap-4">
                    {analyticsCharts?.gender?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Gender</p>
                        <div className="space-y-1.5">
                          {analyticsCharts.gender.map((g: any, i: number) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                                <div className="h-full rounded-full" style={{ width: `${(g.value / totalResponses) * 100}%`, backgroundColor: CHART_COLORS[i] }} />
                              </div>
                              <span className="w-24 text-right text-muted-foreground">{g.name}: {g.value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {analyticsCharts?.income?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Income</p>
                        <div className="space-y-1.5">
                          {analyticsCharts.income.map((inc: any, i: number) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                                <div className="h-full rounded-full" style={{ width: `${(inc.value / totalResponses) * 100}%`, backgroundColor: CHART_COLORS[i] }} />
                              </div>
                              <span className="w-24 text-right text-muted-foreground">{inc.name}: {inc.value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              {activeResultTab === "analytics" && !analytics && (
                <div className="flex flex-col items-center justify-center h-56 text-muted-foreground text-sm">
                  <BarChart2 className="h-10 w-10 mb-3 text-zinc-300" />Run a simulation to see analytics.
                </div>
              )}

              {/* Report tab */}
              {activeResultTab === "report" && (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                  {!report ? (
                    <div className="flex flex-col items-center justify-center h-56 text-muted-foreground text-sm text-center">
                      <FileText className="h-10 w-10 mb-3 text-zinc-300" />
                      <p>Click &quot;Generate Report&quot; to create a structured analysis report.</p>
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {/* Executive Summary */}
                      <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
                        <h4 className="font-semibold text-sm mb-1.5 text-blue-900 dark:text-blue-200">Executive Summary</h4>
                        <p className="text-sm text-blue-800 dark:text-blue-300 leading-relaxed">{report.executive_summary}</p>
                      </div>
                      {/* Key Metrics */}
                      <div>
                        <h4 className="font-semibold text-sm mb-2">Key Metrics</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {Object.entries(report.key_metrics || {}).map(([k, v]: any) => (
                            <div key={k} className="border rounded-lg p-2.5 text-center">
                              <p className="text-xs text-muted-foreground capitalize">{k.replace(/_/g, " ")}</p>
                              <p className="font-bold text-sm mt-0.5">{typeof v === "number" ? (k.includes("rate") || k.includes("confidence") || k.includes("sentiment") ? `${typeof v === "number" && v <= 1 && v >= -1 && k.includes("sentiment") ? (v > 0 ? "+" : "") + v.toFixed(2) : v}` : v) : v}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                      {/* Insights */}
                      {report.key_insights?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Key Insights</h4>
                          <ul className="space-y-1.5">
                            {report.key_insights.map((ins: string, i: number) => (
                              <li key={i} className="flex items-start gap-2 text-sm"><CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />{ins}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {/* Recommendations */}
                      {report.recommendations?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Recommendations</h4>
                          <ul className="space-y-1.5">
                            {report.recommendations.map((rec: string, i: number) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground"><TrendingUp className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {/* Sample Responses */}
                      {report.sample_responses?.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Top Responses (by confidence)</h4>
                          <div className="space-y-2">
                            {report.sample_responses.slice(0, 5).map((r: any, i: number) => (
                              <div key={i} className="border rounded-lg p-3 text-xs space-y-1">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium">{r.persona_label}</span>
                                  <span className={`px-1.5 py-0.5 rounded-full capitalize font-medium ${r.decision === "yes" || r.decision === "stay" ? "bg-green-100 text-green-700" : r.decision === "no" ? "bg-red-100 text-red-700" : "bg-zinc-100 text-zinc-600"}`}>{r.decision}</span>
                                </div>
                                <p className="text-muted-foreground leading-relaxed">{r.response}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
