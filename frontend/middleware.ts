import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });
  let requestCookiesSynced = false;

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set(name, value);

          // Recreate once so downstream handlers receive updated request cookies.
          if (!requestCookiesSynced) {
            supabaseResponse = NextResponse.next({ request });
            requestCookiesSynced = true;
          }

          supabaseResponse.cookies.set(name, value, options);
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set(name, "");

          if (!requestCookiesSynced) {
            supabaseResponse = NextResponse.next({ request });
            requestCookiesSynced = true;
          }

          supabaseResponse.cookies.set(name, "", {
            ...options,
            maxAge: 0,
          });
        },
      },
    }
  );

  // Refresh session so it doesn't expire
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;

  // Protect /dashboard/* routes
  if (pathname.startsWith("/dashboard")) {
    if (!user) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = "/auth/login";
      redirectUrl.searchParams.set("next", pathname);
      const response = NextResponse.redirect(redirectUrl);
      supabaseResponse.cookies
        .getAll()
        .forEach((cookie) => response.cookies.set(cookie));
      return response;
    }
  }

  // Redirect authenticated users away from auth pages
  if (
    user &&
    (pathname.startsWith("/auth/login") || pathname.startsWith("/auth/signup"))
  ) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/dashboard";
    redirectUrl.search = "";
    const response = NextResponse.redirect(redirectUrl);
    supabaseResponse.cookies
      .getAll()
      .forEach((cookie) => response.cookies.set(cookie));
    return response;
  }

  return supabaseResponse;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
