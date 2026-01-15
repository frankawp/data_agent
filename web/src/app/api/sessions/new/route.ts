import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/sessions/new`, {
      method: "POST",
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Create session API error:", error);
    return NextResponse.json(
      { error: "Failed to create new session" },
      { status: 500 }
    );
  }
}
