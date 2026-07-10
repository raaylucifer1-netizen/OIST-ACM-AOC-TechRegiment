"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FolderOpen,
  Plus,
  MoreVertical,
  Loader2,
  Users,
  BarChart,
  Archive,
  Trash2,
  Pencil,
  X,
  FolderArchive,
} from "lucide-react";
import { toast } from "sonner";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewModal, setShowNewModal] = useState(false);
  const [editingProject, setEditingProject] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await api.get("/projects");
      setProjects(res.data.projects || []);
    } catch (err) {
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const openNew = () => {
    setFormName("");
    setFormDesc("");
    setEditingProject(null);
    setShowNewModal(true);
  };

  const openEdit = (project: any) => {
    setFormName(project.name);
    setFormDesc(project.description || "");
    setEditingProject(project);
    setShowNewModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      toast.error("Project name is required");
      return;
    }
    try {
      setSaving(true);
      if (editingProject) {
        await api.put(`/projects/${editingProject.id}`, {
          name: formName.trim(),
          description: formDesc.trim() || null,
        });
        toast.success("Project updated");
      } else {
        await api.post("/projects", {
          name: formName.trim(),
          description: formDesc.trim() || null,
        });
        toast.success("Project created");
      }
      setShowNewModal(false);
      fetchProjects();
    } catch {
      toast.error("Failed to save project");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (project: any) => {
    try {
      await api.post(`/projects/${project.id}/archive`);
      toast.success(project.is_archived ? "Project unarchived" : "Project archived");
      fetchProjects();
    } catch {
      toast.error("Failed to archive project");
    }
  };

  const handleDelete = async (project: any) => {
    if (!confirm(`Delete "${project.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/projects/${project.id}`);
      toast.success("Project deleted");
      fetchProjects();
    } catch {
      toast.error("Failed to delete project");
    }
  };

  const activeProjects = projects.filter((p) => !p.is_archived);
  const archivedProjects = projects.filter((p) => p.is_archived);

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">
            Organize your simulations and personas into focused research projects.
          </p>
        </div>
        <Button onClick={openNew} className="gap-2">
          <Plus className="h-4 w-4" /> New Project
        </Button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : projects.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-16 text-center border-2 border-dashed border-zinc-200 dark:border-zinc-800">
          <div className="h-14 w-14 rounded-full bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center mb-4">
            <FolderOpen className="h-7 w-7 text-zinc-500" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
          <p className="text-sm text-muted-foreground max-w-sm mb-6">
            Create a project to organize your simulations, personas, and reports into a focused
            workspace.
          </p>
          <Button onClick={openNew} className="gap-2">
            <Plus className="h-4 w-4" /> Create Your First Project
          </Button>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Active Projects */}
          {activeProjects.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Active ({activeProjects.length})
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {activeProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onEdit={() => openEdit(project)}
                    onArchive={() => handleArchive(project)}
                    onDelete={() => handleDelete(project)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Archived Projects */}
          {archivedProjects.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <FolderArchive className="h-4 w-4" /> Archived ({archivedProjects.length})
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 opacity-60">
                {archivedProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onEdit={() => openEdit(project)}
                    onArchive={() => handleArchive(project)}
                    onDelete={() => handleDelete(project)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
          <Card className="w-full max-w-md shadow-xl">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{editingProject ? "Edit Project" : "New Project"}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setShowNewModal(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>
                {editingProject
                  ? "Update the project details below."
                  : "Create a new project to organize your research."}
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSave}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Project Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g. Q3 Product Launch Study"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="desc">Description (optional)</Label>
                  <Textarea
                    id="desc"
                    placeholder="What is this project about?"
                    value={formDesc}
                    onChange={(e) => setFormDesc(e.target.value)}
                    rows={3}
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-3 border-t pt-4">
                <Button type="button" variant="outline" onClick={() => setShowNewModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving || !formName.trim()}>
                  {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingProject ? "Save Changes" : "Create Project"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}

function ProjectCard({
  project,
  onEdit,
  onArchive,
  onDelete,
}: {
  project: any;
  onEdit: () => void;
  onArchive: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="flex flex-col hover:border-zinc-400 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-8 w-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0">
              <FolderOpen className="h-4 w-4 text-zinc-600 dark:text-zinc-400" />
            </div>
            <div className="min-w-0">
              <CardTitle className="text-base truncate">{project.name}</CardTitle>
              {project.is_archived && (
                <Badge variant="outline" className="text-xs mt-0.5">
                  Archived
                </Badge>
              )}
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onEdit}>
                <Pencil className="mr-2 h-4 w-4" /> Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onArchive}>
                <Archive className="mr-2 h-4 w-4" />
                {project.is_archived ? "Unarchive" : "Archive"}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600 focus:text-red-600" onClick={onDelete}>
                <Trash2 className="mr-2 h-4 w-4" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        {project.description ? (
          <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
        ) : (
          <p className="text-sm text-muted-foreground italic">No description</p>
        )}
      </CardContent>
      <CardFooter className="border-t pt-3">
        <div className="flex items-center gap-4 text-xs text-muted-foreground w-full">
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            {(project.persona_count || 0).toLocaleString()} personas
          </span>
          <span className="flex items-center gap-1">
            <BarChart className="h-3.5 w-3.5" />
            {(project.simulation_count || 0)} simulations
          </span>
          <span className="ml-auto">
            {new Date(project.updated_at).toLocaleDateString()}
          </span>
        </div>
      </CardFooter>
    </Card>
  );
}
