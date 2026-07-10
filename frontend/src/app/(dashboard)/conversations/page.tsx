"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, MessageSquare, Plus, ArrowRight, ShoppingBag, Calendar } from "lucide-react";
import { toast } from "sonner";

export default function ConversationsPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<any[]>([]);
  const [personas, setPersonas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showNewChatModal, setShowNewChatModal] = useState(false);

  // New conversation form state
  const [selectedPersonaId, setSelectedPersonaId] = useState("");
  const [chatTitle, setChatTitle] = useState("");
  const [productName, setProductName] = useState("");
  const [productDesc, setProductDesc] = useState("");
  const [showProductSection, setShowProductSection] = useState(false);

  useEffect(() => {
    fetchConversations();
    fetchPersonas();
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const res = await api.get("/conversations");
      setConversations(res.data.conversations || []);
    } catch (error) {
      console.error("Failed to fetch conversations", error);
      toast.error("Could not load conversations");
    } finally {
      setLoading(false);
    }
  };

  const fetchPersonas = async () => {
    try {
      const res = await api.get("/personas?page_size=100");
      setPersonas(res.data.personas || []);
    } catch (error) {
      console.error("Failed to fetch personas", error);
    }
  };

  const handleCreateChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPersonaId) {
      toast.error("Please select a persona");
      return;
    }

    try {
      setCreating(true);
      const payload: any = {
        persona_id: selectedPersonaId,
        title: chatTitle.trim() || undefined,
      };

      if (showProductSection && productName.trim()) {
        payload.product_name = productName.trim();
        payload.product_description = productDesc.trim() || undefined;
        if (!payload.title) {
          const selectedPersona = personas.find(p => p.id === selectedPersonaId);
          payload.title = `Product Pitch (${productName}) with ${selectedPersona?.persona_id || "Persona"}`;
        }
      }

      const res = await api.post("/conversations", payload);
      toast.success("Conversation created!");
      setShowNewChatModal(false);
      
      // Redirect to the newly created conversation
      router.push(`/conversations/${res.data.id}`);
    } catch (error) {
      console.error("Failed to create conversation", error);
      toast.error("Failed to start conversation");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Persona Chats</h2>
          <p className="text-muted-foreground">Have a direct conversation with individual personas about any scenario or product.</p>
        </div>
        <Button onClick={() => setShowNewChatModal(true)} className="gap-2">
          <Plus className="h-4 w-4" /> New Conversation
        </Button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : conversations.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-zinc-200 dark:border-zinc-800">
          <div className="h-12 w-12 rounded-full bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center mb-4">
            <MessageSquare className="h-6 w-6 text-zinc-500" />
          </div>
          <CardTitle className="text-lg font-semibold mb-2">No conversations yet</CardTitle>
          <CardDescription className="max-w-sm mb-6">
            Start a direct chat with one of your synthetic personas to understand their perspective or pitch them a product.
          </CardDescription>
          <Button onClick={() => setShowNewChatModal(true)} className="gap-2">
            <Plus className="h-4 w-4" /> Start Your First Chat
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {conversations.map((convo) => {
            const persona = personas.find(p => p.id === convo.persona_id);
            return (
              <Card key={convo.id} className="flex flex-col hover:border-zinc-400 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400 flex items-center justify-center text-xs font-bold">
                        {persona?.persona_id || "P"}
                      </div>
                      <div>
                        <CardTitle className="text-base line-clamp-1">{convo.title}</CardTitle>
                        <CardDescription className="text-xs">
                          {persona ? `${persona.age} • ${persona.gender} • ${persona.city}` : "Unknown Persona"}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pb-3 flex-1 flex flex-col justify-between gap-4">
                  {convo.product_name ? (
                    <div className="flex items-center gap-2 text-xs bg-zinc-50 dark:bg-zinc-900 p-2 rounded border">
                      <ShoppingBag className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
                      <div className="line-clamp-1">
                        <span className="font-semibold">Product:</span> {convo.product_name}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-muted-foreground italic">General conversation</div>
                  )}
                  
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Updated {new Date(convo.updated_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-0">
                  <Button 
                    variant="outline" 
                    className="w-full gap-2 text-xs" 
                    onClick={() => router.push(`/conversations/${convo.id}`)}
                  >
                    Resume Chat <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* New Conversation Modal */}
      {showNewChatModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl border-zinc-200">
            <CardHeader>
              <CardTitle>Start New Conversation</CardTitle>
              <CardDescription>Select a persona from your database to chat with.</CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateChat}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="persona">Target Persona</Label>
                  <Select value={selectedPersonaId} onValueChange={(val: string | null) => setSelectedPersonaId(val || "")}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a persona..." />
                    </SelectTrigger>
                    <SelectContent>
                      {personas.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.persona_id} ({p.age} yr old {p.gender} • {p.occupation} • {p.city})
                        </SelectItem>
                      ))}
                      {personas.length === 0 && (
                        <div className="p-2 text-sm text-center text-muted-foreground">No personas available. Please import some first.</div>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">Chat Title (Optional)</Label>
                  <Input 
                    id="title"
                    placeholder="e.g. Interview with Ramesh"
                    value={chatTitle}
                    onChange={(e) => setChatTitle(e.target.value)}
                  />
                </div>

                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="font-semibold cursor-pointer" onClick={() => setShowProductSection(!showProductSection)}>
                      Show / Pitch a Product
                    </Label>
                    <Button 
                      type="button" 
                      variant="link" 
                      className="h-auto p-0 text-xs" 
                      onClick={() => setShowProductSection(!showProductSection)}
                    >
                      {showProductSection ? "Hide Details" : "Add Product Context"}
                    </Button>
                  </div>
                  
                  {showProductSection && (
                    <div className="space-y-3 p-3 bg-zinc-50 dark:bg-zinc-900/50 rounded border">
                      <div className="space-y-1">
                        <Label htmlFor="prodName" className="text-xs">Product Name</Label>
                        <Input 
                          id="prodName"
                          placeholder="e.g. Electric Scooter Model X"
                          value={productName}
                          onChange={(e) => setProductName(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="prodDesc" className="text-xs">Product Description / Offer Details</Label>
                        <Textarea 
                          id="prodDesc"
                          placeholder="Describe the product, price, features, and target audience..."
                          value={productDesc}
                          onChange={(e) => setProductDesc(e.target.value)}
                          rows={3}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-3 border-t pt-4">
                <Button type="button" variant="outline" onClick={() => setShowNewChatModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={creating || !selectedPersonaId}>
                  {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create & Chat
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
