import fs from "fs";
import path from "path";
import { NextRequest, NextResponse } from "next/server";

import { PROJECT_ROOT } from "../../../lib/commands";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const runId = searchParams.get("runId");
  const target = searchParams.get("target") || "bundle";

  if (!runId || !runId.startsWith("run-")) {
    return new NextResponse("Invalid runId", { status: 400 });
  }

  const runDir = path.join(PROJECT_ROOT, "runs", runId);
  if (!fs.existsSync(runDir)) {
    return new NextResponse("Run directory not found", { status: 404 });
  }

  let filePath = path.join(runDir, "run_bundle.json");

  if (target === "export") {
    const exportDir = path.join(runDir, "project", "export");
    filePath = path.join(exportDir, "game.exe");
    if (!fs.existsSync(filePath)) {
      return new NextResponse("Export binary not found", { status: 404 });
    }
  } else if (!fs.existsSync(filePath)) {
    return new NextResponse("run_bundle.json not found", { status: 404 });
  }

  const stat = fs.statSync(filePath);
  const fileBuffer = fs.readFileSync(filePath);

  const res = new NextResponse(fileBuffer);
  res.headers.set("Content-Type", target === "export" ? "application/octet-stream" : "application/json");
  res.headers.set("Content-Disposition", `attachment; filename="${path.basename(filePath)}"`);
  res.headers.set("Content-Length", stat.size.toString());

  return res;
}
