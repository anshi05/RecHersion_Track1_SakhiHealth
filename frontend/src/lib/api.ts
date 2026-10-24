/** Typed fetch wrapper. Same-origin via the Next rewrite; override with NEXT_PUBLIC_API_BASE. */
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    credentials: "include",
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      body?.error?.code ?? "unknown",
      body?.error?.message ?? res.statusText,
      res.status,
    );
  }
  return res.json() as Promise<T>;
}
