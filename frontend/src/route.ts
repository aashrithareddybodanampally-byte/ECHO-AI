import { useEffect, useState } from "react";

/** Public (logged-out) pages, addressed by URL hash so links and the back button work. */
export type PublicRoute = "home" | "signin" | "signup";

export function parseRoute(hash: string): PublicRoute {
  const path = hash.replace(/^#\/?/, "").split(/[?#]/)[0].toLowerCase();
  if (path === "signin" || path === "signup") return path;
  return "home";
}

export function routeHref(route: PublicRoute): string {
  return route === "home" ? "#/" : `#/${route}`;
}

export function navigate(route: PublicRoute) {
  window.location.hash = routeHref(route);
}

export function useRoute(): PublicRoute {
  const [route, setRoute] = useState<PublicRoute>(() => parseRoute(window.location.hash));
  useEffect(() => {
    const onChange = () => {
      setRoute(parseRoute(window.location.hash));
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
