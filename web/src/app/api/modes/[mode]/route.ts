import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ mode: string }> }
) {
  const { mode } = await params;
  try {
    const response = await fetch(`${BACKEND_URL}/api/modes/${mode}`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch mode" },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ mode: string }> }
) {
  const { mode } = await params;
  try {
    const body = await request.json();
    const response = await fetch(`${BACKEND_URL}/api/modes/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to update mode" },
      { status: 500 }
    );
  }
}
