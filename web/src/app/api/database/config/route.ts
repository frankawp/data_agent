import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// 获取数据库配置状态
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sessionId = searchParams.get("session_id");

  try {
    const url = sessionId
      ? `${BACKEND_URL}/api/database/config?session_id=${sessionId}`
      : `${BACKEND_URL}/api/database/config`;

    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Database config GET error:", error);
    return NextResponse.json(
      { success: false, configured: false, error: "获取配置失败" },
      { status: 500 }
    );
  }
}

// 设置数据库配置
export async function POST(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sessionId = searchParams.get("session_id");

  try {
    const body = await request.json();

    const url = sessionId
      ? `${BACKEND_URL}/api/database/config?session_id=${sessionId}`
      : `${BACKEND_URL}/api/database/config`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Database config POST error:", error);
    return NextResponse.json(
      { success: false, error: "保存配置失败" },
      { status: 500 }
    );
  }
}

// 清除数据库配置
export async function DELETE(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sessionId = searchParams.get("session_id");

  try {
    const url = sessionId
      ? `${BACKEND_URL}/api/database/config?session_id=${sessionId}`
      : `${BACKEND_URL}/api/database/config`;

    const response = await fetch(url, {
      method: "DELETE",
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Database config DELETE error:", error);
    return NextResponse.json(
      { success: false, error: "清除配置失败" },
      { status: 500 }
    );
  }
}
