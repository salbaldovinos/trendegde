import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function proxyRequest(request: NextRequest) {
  const supabase = await createClient()
  const { data: { session } } = await supabase.auth.getSession()

  // Forward the full path to the backend (backend routes are at /api/v1/*)
  const url = new URL(request.url)
  const targetUrl = `${API_URL}${url.pathname}${url.search}`

  // Forward headers, adding Authorization if we have a session
  const headers = new Headers()
  headers.set("Content-Type", request.headers.get("Content-Type") || "application/json")

  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`)
  }

  const body = request.method !== "GET" && request.method !== "HEAD"
    ? await request.text()
    : undefined

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
  })

  const responseBody = await response.text()

  return new NextResponse(responseBody, {
    status: response.status,
    statusText: response.statusText,
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "application/json",
    },
  })
}

export async function GET(request: NextRequest) {
  return proxyRequest(request)
}

export async function POST(request: NextRequest) {
  return proxyRequest(request)
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request)
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request)
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request)
}
