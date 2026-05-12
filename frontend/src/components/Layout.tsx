import { NavLink, Outlet } from "react-router-dom";
import { MessageSquare, Upload, ClipboardList, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { to: "/", label: "Chat", icon: MessageSquare },
  { to: "/ingest", label: "Ingest", icon: Upload },
  { to: "/review", label: "Review Queue", icon: ClipboardList },
];

export function Layout() {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 border-r flex flex-col">
        <div className="p-5 flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="font-bold text-lg tracking-tight">TrustRAG</span>
        </div>
        <Separator />
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <Separator />
        <div className="p-4 text-xs text-muted-foreground">
          API: {(import.meta as unknown as { env: Record<string, string> }).env.VITE_API_URL ?? "localhost:8000"}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
