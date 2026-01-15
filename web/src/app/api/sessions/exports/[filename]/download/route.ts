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
      ? `${BACKEND_URL}/api/sessions/exports/${encodeURIComponent(filename)}/download?session_id=${sessionId}`
      : `${BACKEND_URL}/api/sessions/exports/${encodeURIComponent(filename)}/download`;

    const response = await fetch(url);

    if (!response.ok) {
      return NextResponse.json(
        { error: `文件不存在: ${filename}` },
        { status: response.status }
      );
    }

    // 获取文件内容
    const blob = await response.blob();

    // 返回文件下载响应
    return new NextResponse(blob, {
      headers: {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": `attachment; filename="${encodeURIComponent(filename)}"`,
      },
    });
  } catch (error) {
    console.error("Download API error:", error);
    return NextResponse.json(
      { error: `下载失败: ${(error as Error).message}` },
      { status: 500 }
    );
  }
}
