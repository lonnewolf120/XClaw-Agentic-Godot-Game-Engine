import { NextRequest, NextResponse } from "next/server";

import { listRecentLogs, readLogByName } from "../../../lib/system";

export async function GET(request: NextRequest) {
  const fileName = request.nextUrl.searchParams.get("file");
  const maxLines = Number(request.nextUrl.searchParams.get("maxLines") ?? 200);

  if (fileName) {
    const selected = readLogByName(fileName, Number.isFinite(maxLines) ? maxLines : 200);
    if (!selected) {
      return NextResponse.json({ error: "log file not found" }, { status: 404 });
    }
    return NextResponse.json(selected);
  }

  return NextResponse.json({ logs: listRecentLogs() });
}
