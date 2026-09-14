import { useEffect, useRef } from "react";
import { usePlaybackStore, TIMING } from "@/stores/playback";
import { useUIStore } from "@/stores/ui";

/**
 * Runs the playback animation loop driven by `requestAnimationFrame`.
 * Called only when `status === "playing"`. Pauses the loop otherwise.
 */
export function usePlaybackMachine() {
  const status = usePlaybackStore((s) => s.status);
  const gpuLevel = useUIStore((s) => s.gpuLevel);
  const tick = usePlaybackStore((s) => s.tick);

  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (status !== "playing") return;
    const timing = TIMING[gpuLevel];
    let last = performance.now();

    const loop = (now: number) => {
      const elapsed = now - last;
      const minFrame = Math.max(8, Math.floor(timing.char * 0.6));
      if (elapsed >= minFrame) {
        last = now;
        tick(now);
      }
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, [status, gpuLevel, tick]);
}

export function useFormatTime(completedAt: number, now: number): string {
  const ms = now - completedAt;
  if (ms < 60_000) return "just now";
  if (ms < 3_600_000) return `${Math.floor(ms / 60_000)} min ago`;
  if (ms < 86_400_000) return `${Math.floor(ms / 3_600_000)} hr ago`;
  const days = Math.floor(ms / 86_400_000);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}
