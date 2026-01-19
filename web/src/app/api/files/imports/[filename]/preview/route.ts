import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await params;
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const maxRows = request.nextUrl.searchParams.get("max_rows") || "10";

    let url = `${BACKEND_URL}/api/files/imports/${encodeURIComponent(filename)}/preview?max_rows=${maxRows}`;
    if (sessionId) {
      url += `&session_id=${sessionId}`;
    }

    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Preview API error:", error);
    return NextResponse.json(
      { error: "Failed to preview file" },
      { status: 500 }
    );
  }
}
