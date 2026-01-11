import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from '@/lib/utils/token';

export function middleware(request: NextRequest) {
  const token = getToken() || request.cookies.get('auth_token')?.value;
  const { pathname } = request.nextUrl;

  // Public routes
  const isPublicRoute = pathname === '/login';

  // Redirect to login if not authenticated
  if (!token && !isPublicRoute) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  // Redirect to dashboard if authenticated and on login page
  if (token && isPublicRoute) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
