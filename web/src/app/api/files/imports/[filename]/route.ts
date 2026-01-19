import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// 删除文件
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await params;
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const url = sessionId
      ? `${BACKEND_URL}/api/files/imports/${encodeURIComponent(filename)}?session_id=${sessionId}`
      : `${BACKEND_URL}/api/files/imports/${encodeURIComponent(filename)}`;

    const response = await fetch(url, { method: "DELETE" });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Delete file API error:", error);
    return NextResponse.json(
      { error: "Failed to delete file", success: false },
      { status: 500 }
    );
  }
}
