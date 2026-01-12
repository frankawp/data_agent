import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tableName: string }> }
) {
  const { tableName } = await params;
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/database/tables/${tableName}`
    );
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Table schema API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch table schema" },
      { status: 500 }
    );
  }
}
