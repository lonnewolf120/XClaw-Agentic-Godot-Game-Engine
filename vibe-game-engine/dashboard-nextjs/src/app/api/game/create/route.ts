import { NextRequest, NextResponse } from "next/server";

import { PROJECT_ROOT } from "../../../../lib/commands";
import { GAME_CREATION_MODES } from "../../../../lib/game";
import { startCustomJob } from "../../../../lib/jobs";

const MAX_PROMPT_LENGTH = 1200;

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { prompt?: string; mode?: string };
    const prompt = body.prompt?.trim() ?? "";
    const mode = body.mode ?? "standalone";

    if (!prompt) {
      return NextResponse.json({ error: "prompt is required" }, { status: 400 });
    }

    if (prompt.length > MAX_PROMPT_LENGTH) {
      return NextResponse.json({ error: "prompt is too long" }, { status: 400 });
    }

    if (!GAME_CREATION_MODES.includes(mode as (typeof GAME_CREATION_MODES)[number])) {
      return NextResponse.json({ error: "unsupported mode" }, { status: 400 });
    }

    const pythonExec = process.env.PYTHON || "python";
    const command = [
      pythonExec,
      "scripts/create_game_from_prompt.py",
      "--prompt",
      prompt,
      "--mode",
      mode,
    ];

    const job = startCustomJob("create_game_prompt", command, PROJECT_ROOT);
    return NextResponse.json({ job }, { status: 202 });
  } catch {
    return NextResponse.json({ error: "invalid request" }, { status: 400 });
  }
}
