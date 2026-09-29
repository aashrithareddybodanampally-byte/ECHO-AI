import { describe, expect, it } from "vitest";
import { summarize } from "./faceMood";

const sad = { neutral: 0.1, happy: 0.02, sad: 0.8, angry: 0.03, fearful: 0.02, disgusted: 0.01, surprised: 0.02 };
const neutral = { neutral: 0.7, happy: 0.1, sad: 0.1, angry: 0.03, fearful: 0.03, disgusted: 0.02, surprised: 0.02 };
const flat = { neutral: 0.2, happy: 0.2, sad: 0.2, angry: 0.1, fearful: 0.1, disgusted: 0.1, surprised: 0.1 };

describe("summarize", () => {
  it("averages recent samples and picks the strongest expression", () => {
    const mood = summarize([sad, sad, neutral]);
    expect(mood?.emotion).toBe("sad");
    expect(mood?.confidence).toBeCloseTo((0.8 + 0.8 + 0.1) / 3, 3);
  });

  it("returns null when no face was seen", () => {
    expect(summarize([])).toBeNull();
    expect(summarize([null, null])).toBeNull();
  });

  it("returns null when the face was missing in most frames", () => {
    expect(summarize([sad, null, null, null])).toBeNull();
  });

  it("returns null when the expression is too uncertain", () => {
    expect(summarize([flat, flat])).toBeNull();
  });
});
