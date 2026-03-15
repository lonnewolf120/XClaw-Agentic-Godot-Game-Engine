import { NextResponse } from "next/server";

import { COMMANDS } from "../../../lib/commands";

export async function GET() {
  const commands = Object.entries(COMMANDS).map(([id, value]) => ({ id, label: value.label }));
  return NextResponse.json({ commands });
}
