import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  type NodeProps,
  useNodesState,
  useEdgesState,
} from "reactflow";
import dagre from "dagre";
import {
  User,
  Database,
  Key,
  LinkIcon,
  Type,
  Globe,
  Tag,
  Activity,
  FileText,
  Timer,
  Shield,
} from "lucide-react";
import "reactflow/dist/style.css";

const nodeWidth = 240;
const nodeHeight = 80;

const getLayoutedElements = (nodes: any[], edges: any[], direction = "LR") => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 110,
    ranksep: 180,
    marginx: 60,
    marginy: 60,
  });

  nodes.forEach((n) =>
    dagreGraph.setNode(n.id, { width: nodeWidth, height: nodeHeight })
  );
  edges.forEach((e) => dagreGraph.setEdge(e.source, e.target));

  dagre.layout(dagreGraph);

  const isHorizontal = direction === "LR";
  nodes.forEach((node) => {
    const pos = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;
    node.position = {
      x: pos.x - nodeWidth / 2,
      y: pos.y - nodeHeight / 2,
    };
  });

  return { nodes, edges };
};

const getTypeColor = (type: string) => {
  type = type.toLowerCase();
  if (type.includes("uuid"))
    return "bg-indigo-100 text-indigo-700 border-indigo-200";
  if (
    type.includes("int") ||
    type.includes("bigint") ||
    type.includes("double")
  )
    return "bg-orange-100 text-orange-700 border-orange-200";
  if (
    type.includes("text") ||
    type.includes("varchar") ||
    type.includes("citext")
  )
    return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (type.includes("timestamp") || type.includes("date"))
    return "bg-purple-100 text-purple-700 border-purple-200";
  if (type.includes("bool")) return "bg-pink-100 text-pink-700 border-pink-200";
  if (type.includes("inet")) return "bg-cyan-100 text-cyan-700 border-cyan-200";
  return "bg-gray-100 text-gray-600 border-gray-200";
};

const getFieldIcon = (meta: string) => {
  meta = meta.toUpperCase();
  if (meta.includes("PK")) return <Key size={10} className="text-yellow-600" />;
  if (meta.includes("FK"))
    return <LinkIcon size={10} className="text-blue-600" />;
  return <Type size={10} className="text-gray-500" />;
};

const CustomNode = ({ data }: NodeProps) => {
  const formattedFields = data.fields
    .split("\n")
    .map((line: string, i: number) => {
      const parts = line.trim().split(" ");
      const name = parts.shift();
      const type = parts.join(" ");
      const colorClass = getTypeColor(type);
      const icon = getFieldIcon(type);

      return (
        <div
          key={i}
          className="flex justify-between items-center text-[10px] py-0.5 border-b last:border-none border-gray-200"
        >
          <div className="flex items-center gap-1 font-medium text-gray-800">
            {icon}
            <span>{name}</span>
          </div>
          {type && (
            <span
              className={`text-[9px] px-1.5 py-0.5 rounded-md border ${colorClass}`}
            >
              {type}
            </span>
          )}
        </div>
      );
    });

  return (
    <div
      className="shadow-md rounded-xl border text-xs"
      style={{
        borderColor: data.color,
        background: data.bg,
        width: 240,
      }}
      title={data.desc}
    >
      <div
        className="flex items-center gap-2 font-semibold text-gray-800 border-b border-gray-200 px-2 py-1.5 bg-white/40 rounded-t-xl"
        style={{ color: data.color }}
      >
        {data.icon}
        <span>{data.label}</span>
      </div>

      <div className="px-2 py-1.5 text-gray-700 overflow-hidden">
        {formattedFields}
      </div>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default function ERDiagram() {
  const initialNodes = useMemo(
    () => [
      {
        id: "users",
        type: "custom",
        data: {
          label: "USERS",
          icon: <User size={14} />,
          color: "#2563eb",
          bg: "#dbeafe",
          fields:
            "id UUID PK\nemail CITEXT \np_hash BYTEA\ncreated_at TIMESTAMPTZ\nlast_login_at TIMESTAMPTZ",
          desc: "Registered users of the platform",
        },
      },
      {
        id: "user_session_tokens",
        type: "custom",
        data: {
          label: "SESSION_TOKENS",
          icon: <Shield size={14} />,
          color: "#2563eb",
          bg: "#eff6ff",
          fields:
            "refresh_token TEXT PK\nuser_id UUID FK\ndevice_name TEXT\nexpires_at TIMESTAMPTZ",
          desc: "Active user sessions for authentication",
        },
      },
      {
        id: "user_login_attempts",
        type: "custom",
        data: {
          label: "LOGIN_ATTEMPTS",
          icon: <Shield size={14} />,
          color: "#2563eb",
          bg: "#eff6ff",
          fields:
            "user_id UUID FK\nattempts INT\nlast_failed_login TIMESTAMPTZ",
          desc: "Tracks failed login attempts per user",
        },
      },

      {
        id: "domains",
        type: "custom",
        data: {
          label: "DOMAINS",
          icon: <Globe size={14} />,
          color: "#16a34a",
          bg: "#dcfce7",
          fields: "id BIGINT PK\nurl TEXT\nurl_hash BYTEA\nis_secure BOOLEAN",
          desc: "Root domains registered for shortened URLs",
        },
      },
      {
        id: "urls",
        type: "custom",
        data: {
          label: "URLS",
          icon: <Database size={14} />,
          color: "#16a34a",
          bg: "#bbf7d0",
          fields:
            "id BIGINTPK\ndomain_id BIGINTFK\nshort_code TEXT\noriginal_url TEXT\nclicks BIGINT",
          desc: "Main shortened URL records",
        },
      },
      {
        id: "user_urls",
        type: "custom",
        data: {
          label: "USER_URLS",
          icon: <Database size={14} />,
          color: "#16a34a",
          bg: "#bbf7d0",
          fields:
            "id BIGINT PK\nurl_id BIGINT FK\nuser_id UUID FK\nis_favorite BOOLEAN",
          desc: "User-specific URL associations",
        },
      },
      {
        id: "url_tags",
        type: "custom",
        data: {
          label: "URL_TAGS",
          icon: <Tag size={14} />,
          color: "#9333ea",
          bg: "#f3e8ff",
          fields: "id BIGINT PK\nuser_id UUID FK\nname TEXT\ncolor TEXT",
          desc: "User-defined tags for URL grouping",
        },
      },
      {
        id: "url_tag_relations",
        type: "custom",
        data: {
          label: "TAG_RELATIONS",
          icon: <Tag size={14} />,
          color: "#9333ea",
          bg: "#f5f3ff",
          fields: "url_id BIGINT FK\ntag_id BIGINT FK",
          desc: "Many-to-many relation between URLs and tags",
        },
      },
      {
        id: "url_analytics",
        type: "custom",
        data: {
          label: "URL_ANALYTICS",
          icon: <Activity size={14} />,
          color: "#dc2626",
          bg: "#fee2e2",
          fields:
            "id BIGINT PK\nurl_id BIGINT FK\nclicked_at TIMESTAMPTZ\nip_address INET\ncountry_code TEXT",
          desc: "Click tracking for analytics",
        },
      },
      {
        id: "logs",
        type: "custom",
        data: {
          label: "LOGS",
          icon: <FileText size={14} />,
          color: "#ea580c",
          bg: "#ffedd5",
          fields:
            "id BIGINT PK\nlevel VARCHAR(50)\nmessage TEXT\nuser_id UUID FK\ncreated_at TIMESTAMPTZ",
          desc: "Application logs with user references",
        },
      },
      {
        id: "time_perf",
        type: "custom",
        data: {
          label: "TIME_PERF",
          icon: <Timer size={14} />,
          color: "#ca8a04",
          bg: "#fef9c3",
          fields:
            "id BIGINT PK\nperf_type TEXT\nexecution_time DOUBLE PRECISION\ncreated_at TIMESTAMPTZ",
          desc: "Performance tracking for diagnostics",
        },
      },
    ],
    []
  );

  const initialEdges = useMemo(
    () => [
      {
        id: "u-sessions",
        source: "users",
        target: "user_session_tokens",
        label: "1:N",
      },
      {
        id: "u-login",
        source: "users",
        target: "user_login_attempts",
        label: "1:1",
      },
      { id: "u-urls", source: "users", target: "user_urls", label: "1:N" },
      { id: "u-tags", source: "users", target: "url_tags", label: "1:N" },
      { id: "domains-urls", source: "domains", target: "urls", label: "1:N" },
      {
        id: "urls-userurls",
        source: "urls",
        target: "user_urls",
        label: "1:N",
      },
      {
        id: "urls-tags",
        source: "urls",
        target: "url_tag_relations",
        label: "1:N",
      },
      {
        id: "urls-analytics",
        source: "urls",
        target: "url_analytics",
        label: "1:N",
      },
      {
        id: "tags-relations",
        source: "url_tags",
        target: "url_tag_relations",
        label: "1:N",
      },
      { id: "users-logs", source: "users", target: "logs", label: "1:N" },
    ],
    []
  );

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => getLayoutedElements(initialNodes, initialEdges, "LR"),
    [initialNodes, initialEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(layoutedNodes);
  const [edges, , onEdgesChange] = useEdgesState(layoutedEdges);

  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <ReactFlow
        nodeTypes={{ custom: CustomNode }}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background color="#ccc" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
