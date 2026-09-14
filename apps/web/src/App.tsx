import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useUIStore, type NavPage } from "@/stores/ui";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import Overview from "@/routes/Overview";
import Pipeline from "@/routes/Pipeline";
import FindSolution from "@/routes/FindSolution";
import Chat from "@/routes/Chat";

const PATH_TO_PAGE: Record<string, NavPage> = {
  "/": "overview",
  "/overview": "overview",
  "/pipeline": "pipeline",
  "/find": "find",
  "/chat": "chat",
};

export default function App() {
  const setPage = useUIStore((s) => s.setPage);
  const location = useLocation();

  useEffect(() => {
    const page = PATH_TO_PAGE[location.pathname] ?? "overview";
    setPage(page);
  }, [location.pathname, setPage]);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/find" element={<FindSolution />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
