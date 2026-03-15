import { NextResponse } from "next/server";

import { cancelJob } from "../../../../../lib/jobs";

interface Params {
  params: {
    jobId: string;
  };
}

export async function POST(_request: Request, { params }: Params) {
  try {
    const job = cancelJob(params.jobId);
    return NextResponse.json({ job });
  } catch (error) {
    const message = error instanceof Error ? error.message : "failed to cancel job";
    if (message === "job not found") {
      return NextResponse.json({ error: message }, { status: 404 });
    }
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
