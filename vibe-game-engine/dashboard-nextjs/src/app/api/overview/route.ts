import { NextResponse } from "next/server";

import { buildOverview } from "../../../lib/overview";

export async function GET() {
  return NextResponse.json(buildOverview());
}
