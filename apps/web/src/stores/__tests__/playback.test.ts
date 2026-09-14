import { describe, it, expect, beforeEach } from "vitest";
import { usePlaybackStore } from "@/stores/playback";
import { useUIStore } from "@/stores/ui";

describe("usePlaybackStore", () => {
  beforeEach(() => {
    usePlaybackStore.setState({ ...usePlaybackStore.getState(), views: [], status: "idle", currentIndex: 0, phase: "title", tallyProcessed: 0, tallyAdded: 0, tallyFlagged: 0, tallyRejected: 0, recent: [] });
    useUIStore.setState({ datasetSize: 8, gpuLevel: "GPU Level 2 (Medium)", page: "overview" });
  });

  it("starts in idle state", () => {
    const { status, tallyProcessed } = usePlaybackStore.getState();
    expect(status).toBe("idle");
    expect(tallyProcessed).toBe(0);
  });

  it("reset returns to idle and clears tally", () => {
    const { reset, play, end } = usePlaybackStore.getState();
    play();
    end();
    expect(usePlaybackStore.getState().status).toBe("ended");
    reset();
    const after = usePlaybackStore.getState();
    expect(after.status).toBe("idle");
    expect(after.tallyProcessed).toBe(0);
    expect(after.recent).toHaveLength(0);
  });

  it("play moves status to playing", () => {
    usePlaybackStore.getState().play();
    expect(usePlaybackStore.getState().status).toBe("playing");
  });
});
