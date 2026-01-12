import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const sessionId = searchParams.get("session_id") || "default";

    const response = await fetch(
      `${BACKEND_URL}/api/chat/reset?session_id=${sessionId}`,
      {
        method: "POST",
      }
    );

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Chat reset API proxy error:", error);
    return Response.json(
      { error: "Failed to reset chat" },
      { status: 500 }
    );
  }
}
