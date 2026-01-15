import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    // 获取 session_id 查询参数并传递给后端
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const url = sessionId
      ? `${BACKEND_URL}/api/sessions/exports?session_id=${sessionId}`
      : `${BACKEND_URL}/api/sessions/exports`;

    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Exports API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch exports", files: [] },
      { status: 500 }
    );
  }
}
