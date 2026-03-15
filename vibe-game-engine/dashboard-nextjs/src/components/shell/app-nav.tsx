"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/overview", label: "Overview" },
  { href: "/agents", label: "Agents" },
  { href: "/jobs", label: "Jobs" },
  { href: "/logs", label: "Logs" },
  { href: "/engine", label: "Engine" },
  { href: "/configs", label: "Configs" },
];

export default function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-2">
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`block rounded-lg border px-3 py-2 text-sm transition ${
              active
                ? "border-amber-300/70 bg-amber-300/15 text-amber-100"
                : "border-slate-700 bg-slate-900/70 text-slate-300 hover:border-slate-500"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
