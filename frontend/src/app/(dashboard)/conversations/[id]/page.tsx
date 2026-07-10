"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Send, Loader2, User, MoreVertical } from "lucide-react";

export default function ChatPage() {
  const { id } = useParams();
  const router = useRouter();
  
  const [conversation, setConversation] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversation();
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]); // Auto-scroll when messages update or when typing indicator appears

  const fetchConversation = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/conversations/${id}`);
      setConversation(res.data);
      setMessages(res.data.messages || []);
    } catch (error) {
      console.error("Failed to fetch conversation", error);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const userMessage = input.trim();
    setInput("");
    
    // Optimistic UI update
    const tempId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: tempId,
      role: "user",
      content: userMessage,
      created_at: new Date().toISOString()
    }]);
    
    setSending(true);
    
    try {
      const res = await api.post(`/conversations/${id}/messages`, {
        content: userMessage
      });
      // Append the response from persona
      setMessages(prev => [...prev, res.data]);
    } catch (error) {
      console.error("Failed to send message", error);
      // In a real app, we'd show an error toast here
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <h2 className="text-xl font-semibold">Conversation Not Found</h2>
        <Button onClick={() => router.push("/conversations")} variant="outline">
          Back to Conversations
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto bg-white dark:bg-zinc-950 rounded-xl border overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-zinc-50 dark:bg-zinc-900">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push("/conversations")} className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-700 dark:text-blue-300 font-bold">
              {conversation.persona_label.charAt(0)}
            </div>
            <div>
              <h2 className="font-semibold">{conversation.persona_label}</h2>
              <p className="text-xs text-muted-foreground">{conversation.title}</p>
            </div>
          </div>
        </div>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5 text-muted-foreground" />
        </Button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-zinc-50/50 dark:bg-zinc-950">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 opacity-60">
            <div className="h-12 w-12 rounded-full bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center mb-2">
              <User className="h-6 w-6" />
            </div>
            <p className="text-sm max-w-sm">
              This is the beginning of your conversation with <strong>{conversation.persona_label}</strong>. Say hi!
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div key={msg.id || index} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                <div className={`flex gap-2 max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                  <div className={`h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center mt-auto ${
                    isUser ? "bg-zinc-800 text-white dark:bg-zinc-200 dark:text-black" : "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                  }`}>
                    {isUser ? <User className="h-4 w-4" /> : conversation.persona_label.charAt(0)}
                  </div>
                  <div className={`px-4 py-3 rounded-2xl ${
                    isUser 
                      ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded-br-sm" 
                      : "bg-white dark:bg-zinc-900 border shadow-sm rounded-bl-sm"
                  }`}>
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                    <div className={`text-[10px] mt-1 text-right ${isUser ? "text-zinc-400 dark:text-zinc-500" : "text-zinc-400"}`}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
        
        {sending && (
          <div className="flex justify-start">
            <div className="flex gap-2 max-w-[80%] flex-row">
              <div className="h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center mt-auto bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                {conversation.persona_label.charAt(0)}
              </div>
              <div className="px-5 py-4 rounded-2xl bg-white dark:bg-zinc-900 border shadow-sm rounded-bl-sm flex gap-1 items-center">
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white dark:bg-zinc-950 border-t">
        <div className="relative flex items-center max-w-4xl mx-auto">
          <Textarea 
            placeholder={`Message ${conversation.persona_label.split(' ')[0]}...`}
            className="min-h-[52px] max-h-32 w-full resize-none rounded-xl pr-14 py-3.5"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sending}
          />
          <Button 
            size="icon" 
            className="absolute right-1.5 bottom-1.5 h-10 w-10 rounded-lg transition-all"
            disabled={!input.trim() || sending}
            onClick={handleSend}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="text-center mt-2">
          <span className="text-[10px] text-zinc-400">Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
}
