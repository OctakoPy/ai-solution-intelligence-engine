import { useNavigate } from "react-router-dom";
import { House, Search, MessageCircle, RefreshCw } from "lucide-react";
import { useUIStore, type NavPage } from "@/stores/ui";

const ITEMS: Array<{ id: NavPage; label: string; icon: React.ElementType }> = [
  { id: "overview", label: "Overview", icon: House },
  { id: "pipeline", label: "Ingestion Pipeline", icon: RefreshCw },
  { id: "find", label: "Find a Solution", icon: Search },
  { id: "chat", label: "Chat with the Engine", icon: MessageCircle },
];

const PAGE_PATHS: Record<NavPage, string> = {
  overview: "/overview",
  pipeline: "/pipeline",
  find: "/find",
  chat: "/chat",
};

export function Sidebar() {
  const page = useUIStore((s) => s.page);
  const setPage = useUIStore((s) => s.setPage);
  const navigate = useNavigate();

  const handleNav = (id: NavPage) => {
    setPage(id);
    navigate(PAGE_PATHS[id]);
  };

  return (
    <aside className="flex h-screen w-60 flex-col overflow-y-auto bg-navy-900 p-4 text-white">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-2xl">
          🧠
        </div>
        <span className="text-xs font-bold uppercase tracking-wider leading-tight">ResolveIQ</span>
      </div>
      <nav className="flex flex-col gap-1">
        {ITEMS.map((item) => {
          const active = page === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                active
                  ? "bg-navy-700 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
