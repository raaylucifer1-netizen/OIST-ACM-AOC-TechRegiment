"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Search,
  Filter,
  Loader2,
  ArrowRight,
  Upload,
  X,
  Users,
  TrendingUp,
  MapPin,
  Briefcase,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Database,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

const ALL = "__all__";

export default function PersonasPage() {
  const router = useRouter();

  // List state
  const [personas, setPersonas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [filterOptions, setFilterOptions] = useState<any>({});
  const [filters, setFilters] = useState({
    gender: ALL,
    state: ALL,
    education: ALL,
    lifestyle: ALL,
    technology_adoption: ALL,
    food_preference: ALL,
    age_min: "",
    age_max: "",
    income_min: "",
    income_max: "",
  });

  // Stats state
  const [stats, setStats] = useState<any>(null);
  const [showStats, setShowStats] = useState(false);

  // Import modal state
  const [showImport, setShowImport] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importingFromServer, setImportingFromServer] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const buildParams = useCallback(() => {
    const params: any = { page, page_size: pageSize };
    if (search.trim()) params.search = search.trim();
    if (filters.gender !== ALL) params.gender = filters.gender;
    if (filters.state !== ALL) params.state = filters.state;
    if (filters.education !== ALL) params.education = filters.education;
    if (filters.lifestyle !== ALL) params.lifestyle = filters.lifestyle;
    if (filters.technology_adoption !== ALL) params.technology_adoption = filters.technology_adoption;
    if (filters.food_preference !== ALL) params.food_preference = filters.food_preference;
    if (filters.age_min) params.age_min = filters.age_min;
    if (filters.age_max) params.age_max = filters.age_max;
    if (filters.income_min) params.income_min = filters.income_min;
    if (filters.income_max) params.income_max = filters.income_max;
    return params;
  }, [page, search, filters]);

  const fetchPersonas = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/personas", { params: buildParams() });
      setPersonas(res.data.personas);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch {
      toast.error("Failed to fetch personas");
    } finally {
      setLoading(false);
    }
  }, [buildParams]);

  const fetchFilterOptions = async () => {
    try {
      const res = await api.get("/personas/filter-options/values");
      setFilterOptions(res.data);
    } catch {}
  };

  const fetchStats = async () => {
    try {
      const res = await api.get("/personas/stats");
      setStats(res.data);
    } catch {}
  };

  // Reset page on search/filter change
  useEffect(() => { setPage(1); }, [search, filters]);

  useEffect(() => {
    const t = setTimeout(() => fetchPersonas(), 300);
    return () => clearTimeout(t);
  }, [fetchPersonas]);

  useEffect(() => {
    fetchFilterOptions();
    fetchStats();
  }, []);

  const activeFilterCount = Object.entries(filters).filter(
    ([k, v]) => v !== ALL && v !== ""
  ).length;

  const resetFilters = () =>
    setFilters({
      gender: ALL, state: ALL, education: ALL, lifestyle: ALL,
      technology_adoption: ALL, food_preference: ALL,
      age_min: "", age_max: "", income_min: "", income_max: "",
    });

  // Import handlers
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) { setImportFile(f); setImportResult(null); }
  };

  const handleUploadImport = async () => {
    if (!importFile) return;
    const form = new FormData();
    form.append("file", importFile);
    try {
      setImporting(true);
      setImportResult(null);
      const res = await api.post("/personas/import", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportResult(res.data);
      if (res.data.imported > 0) {
        toast.success(`Imported ${res.data.imported.toLocaleString()} personas!`);
        fetchPersonas();
        fetchStats();
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleServerImport = async () => {
    try {
      setImportingFromServer(true);
      setImportResult(null);
      const res = await api.post("/personas/import/from-server");
      setImportResult(res.data);
      if (res.data.imported > 0) {
        toast.success(`Imported ${res.data.imported.toLocaleString()} personas from server CSV!`);
        fetchPersonas();
        fetchStats();
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Server import failed");
    } finally {
      setImportingFromServer(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Personas Database {total > 0 && `(${total.toLocaleString()})`}
          </h2>
          <p className="text-muted-foreground">Browse, filter, and manage your synthetic population.</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => { setShowStats(!showStats); if (!stats) fetchStats(); }}
          >
            <TrendingUp className="h-4 w-4" />
            {showStats ? "Hide Stats" : "Show Stats"}
          </Button>
          <Button className="gap-2" onClick={() => { setShowImport(true); setImportResult(null); setImportFile(null); }}>
            <Upload className="h-4 w-4" /> Import Personas
          </Button>
        </div>
      </div>

      {/* Stats Panel */}
      {showStats && stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Users className="h-4 w-4" /> Total Personas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{(stats.total_personas || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground mt-1">Avg age: {stats.avg_age} yrs</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Users className="h-4 w-4" /> Gender Split
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                {Object.entries(stats.gender_distribution || {}).map(([g, c]: any) => (
                  <div key={g} className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-zinc-800 rounded-full"
                        style={{ width: `${(c / stats.total_personas) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs w-20 text-right">{g}: {c.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <MapPin className="h-4 w-4" /> Top States
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {Object.entries(stats.state_distribution || {}).slice(0, 4).map(([s, c]: any) => (
                  <div key={s} className="flex justify-between text-xs">
                    <span className="text-muted-foreground truncate">{s}</span>
                    <span className="font-medium">{c.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Briefcase className="h-4 w-4" /> Top Occupations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {(stats.top_occupations || []).slice(0, 4).map((o: any) => (
                  <div key={o.occupation} className="flex justify-between text-xs">
                    <span className="text-muted-foreground truncate">{o.occupation}</span>
                    <span className="font-medium">{o.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Table Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by ID, city, occupation, brand..."
                className="pl-8"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button
              variant={showFilters ? "default" : "outline"}
              className="gap-2 relative"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
              Filters
              {activeFilterCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
              {showFilters ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </Button>
            {activeFilterCount > 0 && (
              <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground" onClick={resetFilters}>
                <X className="h-3 w-3" /> Clear filters
              </Button>
            )}
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <FilterSelect
                label="Gender"
                value={filters.gender}
                options={filterOptions.genders || []}
                onChange={(v) => setFilters({ ...filters, gender: v })}
              />
              <FilterSelect
                label="State"
                value={filters.state}
                options={filterOptions.states || []}
                onChange={(v) => setFilters({ ...filters, state: v })}
              />
              <FilterSelect
                label="Education"
                value={filters.education}
                options={filterOptions.educations || []}
                onChange={(v) => setFilters({ ...filters, education: v })}
              />
              <FilterSelect
                label="Lifestyle"
                value={filters.lifestyle}
                options={filterOptions.lifestyles || []}
                onChange={(v) => setFilters({ ...filters, lifestyle: v })}
              />
              <FilterSelect
                label="Tech Adoption"
                value={filters.technology_adoption}
                options={filterOptions.technology_adoptions || []}
                onChange={(v) => setFilters({ ...filters, technology_adoption: v })}
              />
              <FilterSelect
                label="Food Preference"
                value={filters.food_preference}
                options={filterOptions.food_preferences || []}
                onChange={(v) => setFilters({ ...filters, food_preference: v })}
              />
              <div className="space-y-1">
                <Label className="text-xs">Age Range</Label>
                <div className="flex gap-1">
                  <Input
                    type="number"
                    placeholder="Min"
                    className="h-9"
                    value={filters.age_min}
                    onChange={(e) => setFilters({ ...filters, age_min: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Max"
                    className="h-9"
                    value={filters.age_max}
                    onChange={(e) => setFilters({ ...filters, age_max: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Income (₹)</Label>
                <div className="flex gap-1">
                  <Input
                    type="number"
                    placeholder="Min"
                    className="h-9"
                    value={filters.income_min}
                    onChange={(e) => setFilters({ ...filters, income_min: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Max"
                    className="h-9"
                    value={filters.income_max}
                    onChange={(e) => setFilters({ ...filters, income_max: e.target.value })}
                  />
                </div>
              </div>
            </div>
          )}
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-md border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-50 dark:bg-zinc-900">
                      <TableHead className="w-24">ID</TableHead>
                      <TableHead>Demographics</TableHead>
                      <TableHead>Occupation</TableHead>
                      <TableHead>Income</TableHead>
                      <TableHead>Personality</TableHead>
                      <TableHead>Lifestyle</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {personas.map((persona) => (
                      <TableRow
                        key={persona.id}
                        className="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/50"
                        onClick={() => router.push(`/personas/${persona.id}`)}
                      >
                        <TableCell className="font-mono font-medium text-sm">{persona.persona_id}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-sm">{persona.age} yrs · {persona.gender}</span>
                            <span className="text-xs text-muted-foreground">{persona.city}, {persona.state}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-sm">{persona.occupation}</span>
                            <span className="text-xs text-muted-foreground">{persona.education}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm font-medium">
                          ₹{(persona.income_inr / 100000).toFixed(1)}L
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1 flex-wrap">
                            <TraitDot label="O" value={persona.openness} />
                            <TraitDot label="C" value={persona.conscientiousness} />
                            <TraitDot label="E" value={persona.extraversion} />
                            <TraitDot label="A" value={persona.agreeableness} />
                            <TraitDot label="N" value={persona.neuroticism} />
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-xs">{persona.lifestyle}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); router.push(`/personas/${persona.id}`); }}
                          >
                            View <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {personas.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                          {total === 0
                            ? "No personas imported yet. Click \"Import Personas\" to get started."
                            : "No personas match your current filters."}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>

              {total > 0 && (
                <div className="flex items-center justify-between py-1">
                  <p className="text-sm text-muted-foreground">
                    Showing <span className="font-medium">{(page - 1) * pageSize + 1}</span>–
                    <span className="font-medium">{Math.min(page * pageSize, total)}</span> of{" "}
                    <span className="font-medium">{total.toLocaleString()}</span>
                  </p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1}>
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      {page} / {totalPages}
                    </span>
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(p + 1, totalPages))} disabled={page === totalPages}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Import Modal */}
      {showImport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-zinc-950 rounded-xl border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between p-5 border-b">
              <div>
                <h3 className="font-semibold text-lg">Import Personas</h3>
                <p className="text-sm text-muted-foreground">Upload a CSV/Excel file or load from server.</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowImport(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="p-5 space-y-5">
              {/* Server import */}
              <div className="rounded-lg border bg-zinc-50 dark:bg-zinc-900 p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <Database className="h-5 w-5 text-zinc-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Load from Server Database</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Instantly import the 20,000 pre-loaded personas from the server CSV at{" "}
                      <code className="bg-zinc-200 dark:bg-zinc-800 px-1 rounded text-[11px]">
                        D:\AARU\backend\data\
                      </code>
                    </p>
                  </div>
                </div>
                <Button
                  className="w-full gap-2"
                  onClick={handleServerImport}
                  disabled={importingFromServer || importing}
                >
                  {importingFromServer ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Importing 20,000 personas...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4" />
                      Import from Server CSV (20,000 personas)
                    </>
                  )}
                </Button>
              </div>

              <div className="relative flex items-center gap-3">
                <div className="flex-1 border-t" />
                <span className="text-xs text-muted-foreground">or upload your own file</span>
                <div className="flex-1 border-t" />
              </div>

              {/* File upload */}
              <div className="space-y-3">
                <div
                  className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-zinc-400 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm font-medium">
                    {importFile ? importFile.name : "Click to upload CSV or Excel"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Supports .csv, .xlsx, .xls — must match the 42-column schema
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </div>
                {importFile && (
                  <Button
                    className="w-full gap-2"
                    onClick={handleUploadImport}
                    disabled={importing || importingFromServer}
                  >
                    {importing ? (
                      <><Loader2 className="h-4 w-4 animate-spin" />Importing...</>
                    ) : (
                      <><Upload className="h-4 w-4" />Import {importFile.name}</>
                    )}
                  </Button>
                )}
              </div>

              {/* Import result */}
              {importResult && (
                <div
                  className={`rounded-lg border p-4 space-y-2 ${
                    importResult.status === "failed"
                      ? "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
                      : "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {importResult.status === "failed" ? (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    )}
                    <span className="font-medium text-sm">
                      {importResult.status === "failed"
                        ? "Import Failed"
                        : `Import Complete — ${importResult.imported?.toLocaleString()} personas added`}
                    </span>
                  </div>
                  {importResult.failed > 0 && (
                    <p className="text-xs text-muted-foreground">{importResult.failed} rows failed to import.</p>
                  )}
                  {importResult.errors?.slice(0, 3).map((e: string, i: number) => (
                    <p key={i} className="text-xs text-red-600">{e}</p>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end p-5 border-t">
              <Button variant="outline" onClick={() => setShowImport(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-xs">{label}</Label>
      <Select value={value} onValueChange={(v: string | null) => onChange(v ?? ALL)}>
        <SelectTrigger className="h-9">
          <SelectValue placeholder={`All ${label}s`} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All {label}s</SelectItem>
          {options.map((o: string) => (
            <SelectItem key={o} value={o}>{o}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function TraitDot({ label, value }: { label: string; value: number }) {
  const color =
    value >= 70 ? "bg-green-500" : value >= 40 ? "bg-yellow-400" : "bg-red-400";
  return (
    <span title={`${label}: ${value}`} className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </span>
  );
}
