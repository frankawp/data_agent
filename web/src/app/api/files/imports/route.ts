import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const url = sessionId
      ? `${BACKEND_URL}/api/files/imports?session_id=${sessionId}`
      : `${BACKEND_URL}/api/files/imports`;

    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Imports API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch imports", files: [] },
      { status: 500 }
    );
  }
}
