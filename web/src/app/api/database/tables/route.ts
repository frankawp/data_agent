import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sessionId = searchParams.get("session_id");

  try {
    const url = sessionId
      ? `${BACKEND_URL}/api/database/tables?session_id=${sessionId}`
      : `${BACKEND_URL}/api/database/tables`;

    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Database tables API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch tables", tables: [] },
      { status: 500 }
    );
  }
}
