import Link from "next/link";
import { ArrowRight, Bot, Users, Activity } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-3xl space-y-8">
        <div className="flex justify-center mb-8">
          <div className="h-16 w-16 bg-blue-600 rounded-2xl flex items-center justify-center rotate-3 shadow-xl">
            <span className="text-3xl font-black text-white tracking-tighter -rotate-3">A</span>
          </div>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-zinc-900 dark:text-white">
          Synthetic Human <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
            Population Simulator
          </span>
        </h1>
        
        <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto leading-relaxed">
          Aaru India is an advanced agentic AI platform designed to simulate realistic human populations, interactions, and societal dynamics.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-4 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-xl font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-lg shadow-zinc-200 dark:shadow-none"
          >
            Access Platform <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/register"
            className="w-full sm:w-auto px-8 py-4 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white border border-zinc-200 dark:border-zinc-800 rounded-xl font-semibold hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-all flex items-center justify-center"
          >
            Create Account
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 text-left">
          <div className="p-6 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-sm">
            <Users className="h-8 w-8 text-blue-500 mb-4" />
            <h3 className="font-bold text-lg mb-2">Diverse Personas</h3>
            <p className="text-zinc-500 dark:text-zinc-400 text-sm">Simulate specific demographics with highly detailed, culturally accurate AI personas.</p>
          </div>
          <div className="p-6 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-sm">
            <Activity className="h-8 w-8 text-purple-500 mb-4" />
            <h3 className="font-bold text-lg mb-2">Behavioral Dynamics</h3>
            <p className="text-zinc-500 dark:text-zinc-400 text-sm">Observe complex interactions, group dynamics, and emergent behaviors in controlled environments.</p>
          </div>
          <div className="p-6 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-sm">
            <Bot className="h-8 w-8 text-orange-500 mb-4" />
            <h3 className="font-bold text-lg mb-2">Agentic Workflows</h3>
            <p className="text-zinc-500 dark:text-zinc-400 text-sm">Leverage sophisticated LLMs to drive autonomous, goal-oriented synthetic agents.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
