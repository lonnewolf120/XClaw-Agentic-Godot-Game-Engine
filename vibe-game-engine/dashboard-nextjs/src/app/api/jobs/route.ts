import { NextResponse } from "next/server";

import { listJobs } from "../../../lib/jobs";

export async function GET() {
  return NextResponse.json({ jobs: listJobs() });
}
