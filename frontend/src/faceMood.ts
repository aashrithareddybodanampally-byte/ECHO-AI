/**
 * Optional camera mood: estimates facial expression in the browser with face-api.
 *
 * Privacy: video frames never leave the device. Only the averaged expression
 * label and its confidence are sent with a chat message, and only while the
 * user has the camera switched on.
 */

export type ExpressionScores = Record<string, number>;

export interface FaceMood {
  emotion: string;
  confidence: number;
}

/** Number of recent samples averaged (about 5 seconds at one sample every 700 ms). */
export const WINDOW = 7;
export const SAMPLE_INTERVAL_MS = 700;
/** Below this averaged confidence the expression is too uncertain to send. */
export const MIN_CONFIDENCE = 0.35;
/** Share of recent samples that must contain a face. */
export const MIN_FACE_RATIO = 0.5;

/** Average the recent expression samples (null = no face in that frame). */
export function summarize(samples: (ExpressionScores | null)[]): FaceMood | null {
  const faces = samples.filter((s): s is ExpressionScores => s !== null);
  if (faces.length === 0 || faces.length / samples.length < MIN_FACE_RATIO) return null;
  const totals: ExpressionScores = {};
  for (const scores of faces) {
    for (const [label, value] of Object.entries(scores)) totals[label] = (totals[label] ?? 0) + value;
  }
  let best: FaceMood | null = null;
  for (const [label, total] of Object.entries(totals)) {
    const mean = total / faces.length;
    if (!best || mean > best.confidence) best = { emotion: label, confidence: mean };
  }
  if (!best || best.confidence < MIN_CONFIDENCE) return null;
  return { emotion: best.emotion, confidence: Math.round(best.confidence * 1000) / 1000 };
}

type FaceApi = typeof import("@vladmandic/face-api");

export class CameraMood {
  private faceapi: FaceApi | null = null;
  private stream: MediaStream | null = null;
  private timer: number | null = null;
  private samples: (ExpressionScores | null)[] = [];

  constructor(private modelUrl = "/models/face-api") {}

  /** Ask for the camera, load the models and start sampling into `video`. */
  async start(video: HTMLVideoElement, onUpdate: (mood: FaceMood | null) => void) {
    const faceapi = this.faceapi ?? (await import("@vladmandic/face-api"));
    this.faceapi = faceapi;
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(this.modelUrl),
      faceapi.nets.faceExpressionNet.loadFromUri(this.modelUrl),
    ]);
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: "user" },
      audio: false,
    });
    video.srcObject = this.stream;
    await video.play();

    const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });
    const tick = async () => {
      if (!this.stream) return;
      const result = await faceapi.detectSingleFace(video, options).withFaceExpressions();
      this.samples = [...this.samples, result ? { ...result.expressions } : null].slice(-WINDOW);
      onUpdate(this.current());
      if (this.stream) this.timer = window.setTimeout(tick, SAMPLE_INTERVAL_MS);
    };
    void tick();
  }

  current(): FaceMood | null {
    return summarize(this.samples);
  }

  stop() {
    if (this.timer !== null) window.clearTimeout(this.timer);
    this.timer = null;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.samples = [];
  }
}
