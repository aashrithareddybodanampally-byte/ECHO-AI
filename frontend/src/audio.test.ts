import { describe, expect, it } from "vitest";
import { encodeWav, mixToMono } from "./audio";

describe("encodeWav", () => {
  it("writes a valid 16-bit mono PCM header", () => {
    const buffer = encodeWav(new Float32Array([0, 0.5, -0.5, 1]), 16000);
    const view = new DataView(buffer);
    const text = (o: number, n: number) =>
      String.fromCharCode(...new Uint8Array(buffer, o, n));
    expect(buffer.byteLength).toBe(44 + 4 * 2);
    expect(text(0, 4)).toBe("RIFF");
    expect(text(8, 4)).toBe("WAVE");
    expect(view.getUint16(20, true)).toBe(1); // PCM
    expect(view.getUint16(22, true)).toBe(1); // mono
    expect(view.getUint32(24, true)).toBe(16000);
    expect(view.getUint16(34, true)).toBe(16);
    expect(view.getUint32(40, true)).toBe(8);
  });

  it("clips and scales samples", () => {
    const view = new DataView(encodeWav(new Float32Array([2, -2, 0]), 8000));
    expect(view.getInt16(44, true)).toBe(0x7fff);
    expect(view.getInt16(46, true)).toBe(-0x8000);
    expect(view.getInt16(48, true)).toBe(0);
  });
});

describe("mixToMono", () => {
  it("averages channels", () => {
    const out = mixToMono([new Float32Array([1, 0]), new Float32Array([0, 1])]);
    expect(Array.from(out)).toEqual([0.5, 0.5]);
  });
});
