import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/database/tables`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Database tables API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch tables", tables: [] },
      { status: 500 }
    );
  }
}
