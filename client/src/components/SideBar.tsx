import { useView } from "../context/ViewContext";
import { Link2, BarChart3, Tag, Database, GitBranch, Network } from "lucide-react";

export default function SideBar() {
  const { view, setView } = useView();

  return (
    <aside className="w-full md:w-64 flex-shrink-0">
      <nav className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-2">
        <button
          onClick={() => setView("urls")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
            view === "urls"
              ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
              : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
          }`}
        >
          <Link2 className="w-5 h-5" />
          My URLs
        </button>
        <button
          onClick={() => setView("tags")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
            view === "tags"
              ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
              : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
          }`}
        >
          <Tag className="w-5 h-5" />
          Tags
        </button>
        <button
          onClick={() => setView("dashboard")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
            view === "dashboard"
              ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
              : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
          }`}
        >
          <BarChart3 className="w-5 h-5" />
          Dashboard
        </button>
        <button
          onClick={() => setView("db")}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
            view === "db"
              ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
              : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
          }`}
        >
          <Database className="w-5 h-5" />
          Database
        </button>

        <button
            onClick={() => setView("api")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
              view === "api"
                ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
                : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
            }`}
          >
        <Network className="w-5 h-5" />
          API
        </button>
        
        <button
            onClick={() => window.open("https://github.com/VitorTz/Haar", "_blank")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
              view === "github"
                ? "bg-indigo-50 text-indigo-600 font-medium shadow-sm"
                : "text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98"
            }`}
          >
        <GitBranch className="w-5 h-5" />
          GitHub
        </button>

      </nav>
    </aside>
  );
}
