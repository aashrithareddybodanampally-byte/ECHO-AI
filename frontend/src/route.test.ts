import { describe, expect, it } from "vitest";
import { parseRoute, routeHref } from "./route";

describe("parseRoute", () => {
  it.each([
    ["", "home"],
    ["#", "home"],
    ["#/", "home"],
    ["#/signin", "signin"],
    ["#/SignUp", "signup"],
    ["#/signup?next=chat", "signup"],
    ["#/unknown", "home"],
  ])("%s -> %s", (hash, route) => {
    expect(parseRoute(hash)).toBe(route);
  });

  it("round-trips with routeHref", () => {
    for (const route of ["home", "signin", "signup"] as const) {
      expect(parseRoute(routeHref(route))).toBe(route);
    }
  });
});
