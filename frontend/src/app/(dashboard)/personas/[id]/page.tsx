"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Loader2, BrainCircuit, Activity, MessageSquare } from "lucide-react";
import { toast } from "sonner";

export default function PersonaDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [persona, setPersona] = useState<any>(null);
  const [adjacent, setAdjacent] = useState<{ prev_id: string | null, next_id: string | null }>({ prev_id: null, next_id: null });
  const [loading, setLoading] = useState(true);
  const [startingChat, setStartingChat] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    fetchPersona();
  }, [id]);

  const handleChatWithPersona = async () => {
    try {
      setChatLoading(true);
      const res = await api.post("/conversations", {
        persona_id: id,
        title: `Chat with ${persona.persona_id}`
      });
      router.push(`/conversations/${res.data.id}`);
    } catch (error) {
      console.error("Failed to start chat", error);
      toast.error("Failed to start chat with this persona");
    } finally {
      setChatLoading(false);
    }
  };

  const fetchPersona = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/personas/${id}`);
      setPersona(res.data);
      
      try {
        const adjRes = await api.get(`/personas/${id}/adjacent`);
        setAdjacent(adjRes.data);
      } catch (adjErr) {
        console.error("Failed to fetch adjacent personas", adjErr);
      }
    } catch (error) {
      console.error("Failed to fetch persona", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async () => {
    try {
      setStartingChat(true);
      const res = await api.post("/conversations", { persona_id: id });
      router.push(`/conversations/${res.data.id}`);
    } catch (error) {
      console.error("Failed to start chat", error);
      setStartingChat(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <h2 className="text-xl font-semibold">Persona Not Found</h2>
        <Button onClick={() => router.push("/personas")} variant="outline">
          Back to Database
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/personas")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Persona {persona.persona_id}</h2>
            <p className="text-muted-foreground">{persona.occupation} from {persona.city}, {persona.state}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={!adjacent.prev_id}
            onClick={() => adjacent.prev_id && router.push(`/personas/${adjacent.prev_id}`)}
          >
            Previous
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            disabled={!adjacent.next_id}
            onClick={() => adjacent.next_id && router.push(`/personas/${adjacent.next_id}`)}
          >
            Next
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Demographics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Age</span>
              <span className="font-medium">{persona.age}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Gender</span>
              <span className="font-medium">{persona.gender}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Marital Status</span>
              <span className="font-medium">{persona.marital_status} ({persona.children} children)</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Education</span>
              <span className="font-medium">{persona.education}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Income</span>
              <span className="font-medium">₹{persona.income_inr.toLocaleString()}</span>
            </div>
            <div className="flex justify-between pb-2">
              <span className="text-muted-foreground">Languages</span>
              <span className="font-medium text-right">{persona.language}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Psychographics & Behavior</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="shopping">
              <TabsList className="mb-4">
                <TabsTrigger value="shopping">Shopping</TabsTrigger>
                <TabsTrigger value="media">Media & Tech</TabsTrigger>
                <TabsTrigger value="finance">Finance</TabsTrigger>
                <TabsTrigger value="health">Health</TabsTrigger>
              </TabsList>
              
              <TabsContent value="shopping" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Lifestyle</span>
                    <p className="font-medium">{persona.lifestyle}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Shopping Frequency</span>
                    <p className="font-medium">{persona.shopping_frequency}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Brand Preference</span>
                    <p className="font-medium">{persona.preferred_brand}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Online vs Offline</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-full bg-zinc-200 rounded-full overflow-hidden flex">
                        <div className="bg-blue-500 h-full" style={{ width: `${persona.online_shopping_pct}%` }}></div>
                        <div className="bg-orange-500 h-full" style={{ width: `${persona.offline_shopping_pct}%` }}></div>
                      </div>
                      <span className="text-xs">{persona.online_shopping_pct}% Online</span>
                    </div>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="media" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Tech Adoption</span>
                    <p className="font-medium">{persona.technology_adoption}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Primary Device</span>
                    <p className="font-medium">{persona.smartphone_brand}</p>
                  </div>
                  <div className="col-span-2 mt-4">
                    <span className="text-sm text-muted-foreground block mb-2">Media Consumption (%)</span>
                    <div className="grid grid-cols-4 gap-2 text-center text-sm">
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.social_media_pct}%</div>
                        <div className="text-xs text-muted-foreground">Social</div>
                      </div>
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.ott_pct}%</div>
                        <div className="text-xs text-muted-foreground">OTT</div>
                      </div>
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.tv_pct}%</div>
                        <div className="text-xs text-muted-foreground">TV</div>
                      </div>
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.print_pct}%</div>
                        <div className="text-xs text-muted-foreground">Print</div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="finance" className="space-y-4">
                 <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Preferred Payment</span>
                    <p className="font-medium">{persona.payment_method}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Risk Appetite</span>
                    <p className="font-medium">{persona.investment_risk_appetite}</p>
                  </div>
                  <div className="col-span-2 mt-4">
                    <span className="text-sm text-muted-foreground block mb-2">Financial Allocation (%)</span>
                    <div className="grid grid-cols-4 gap-2 text-center text-sm">
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.savings_pct}%</div>
                        <div className="text-xs text-muted-foreground">Savings</div>
                      </div>
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.investment_pct}%</div>
                        <div className="text-xs text-muted-foreground">Investments</div>
                      </div>
                      <div className="bg-zinc-100 p-2 rounded">
                        <div className="font-bold">{persona.expenses_pct}%</div>
                        <div className="text-xs text-muted-foreground">Expenses</div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="health" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Dietary Preference</span>
                    <p className="font-medium">{persona.food_preference}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Health Consciousness</span>
                    <p className="font-medium">{persona.health_consciousness}</p>
                  </div>
                </div>
              </TabsContent>

            </Tabs>
          </CardContent>
        </Card>
      </div>
      
      <div className="flex gap-4">
        <Button className="flex-1" variant="outline">
          <BrainCircuit className="mr-2 h-4 w-4" />
          View Memories
        </Button>
        <Button className="flex-1" variant="outline">
          <Activity className="mr-2 h-4 w-4" />
          View History
        </Button>
        <Button className="flex-1" onClick={handleStartChat} disabled={startingChat}>
          {startingChat ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <MessageSquare className="mr-2 h-4 w-4" />
          )}
          {startingChat ? "Starting Chat..." : "Chat with Persona"}
        </Button>
      </div>
    </div>
  );
}
