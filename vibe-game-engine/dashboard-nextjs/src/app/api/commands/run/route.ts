import { NextRequest, NextResponse } from "next/server";

import { startJob } from "../../../../lib/jobs";

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { commandId?: string };
    if (!body.commandId) {
      return NextResponse.json({ error: "commandId is required" }, { status: 400 });
    }
    const job = startJob(body.commandId);
    return NextResponse.json({ job }, { status: 202 });
  } catch {
    return NextResponse.json({ error: "invalid request" }, { status: 400 });
  }
}
