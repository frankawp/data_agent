import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/sessions`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Sessions API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch session info" },
      { status: 500 }
    );
  }
}
