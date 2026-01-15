import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await context.params;

    // 获取 session_id 查询参数并传递给后端
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const url = sessionId
      ? `${BACKEND_URL}/api/sessions/exports/${encodeURIComponent(filename)}/preview?session_id=${sessionId}`
      : `${BACKEND_URL}/api/sessions/exports/${encodeURIComponent(filename)}/preview`;

    const response = await fetch(url);

    if (!response.ok) {
      return NextResponse.json(
        { content: `文件不存在: ${filename}`, type: "text" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Preview API error:", error);
    return NextResponse.json(
      { content: `预览失败: ${(error as Error).message}`, type: "text" },
      { status: 500 }
    );
  }
}
