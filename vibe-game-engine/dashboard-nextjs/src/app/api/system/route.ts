import { NextResponse } from "next/server";

import { buildSystemSnapshot } from "../../../lib/system";

export async function GET() {
  return NextResponse.json(buildSystemSnapshot());
}
