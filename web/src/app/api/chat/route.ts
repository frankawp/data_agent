import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// 设置更长的超时时间（5分钟），支持复杂分析任务
export const maxDuration = 300;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // 使用 AbortController 设置 5 分钟超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);

    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // 如果是流式响应，直接转发
    if (body.stream) {
      return new Response(response.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }

    // 非流式响应
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Chat API proxy error:", error);
    return Response.json(
      { error: "Failed to connect to backend" },
      { status: 500 }
    );
  }
}
