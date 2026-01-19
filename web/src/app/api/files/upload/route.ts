import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const sessionId = request.nextUrl.searchParams.get("session_id");
    const url = sessionId
      ? `${BACKEND_URL}/api/files/upload?session_id=${sessionId}`
      : `${BACKEND_URL}/api/files/upload`;

    // 获取表单数据并转发到后端
    const formData = await request.formData();

    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Upload API error:", error);
    return NextResponse.json(
      { error: "Failed to upload file", success: false },
      { status: 500 }
    );
  }
}
