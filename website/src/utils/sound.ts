// Web Audio API Synthesized Sound Effects (No external assets required, 0ms latency)

class SoundManager {
  private ctx: AudioContext | null = null;
  private tickBuffer: AudioBuffer | null = null;
  private isTickLoading = false;

  private getContext(): AudioContext | null {
    if (typeof window === "undefined") return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  constructor() {
    if (typeof window !== "undefined") {
      const unlockAudio = () => {
        this.getContext();
        this.preloadTick();
      };
      window.addEventListener("pointerdown", unlockAudio, { once: true });
      window.addEventListener("wheel", unlockAudio, { once: true });
      window.addEventListener("keydown", unlockAudio, { once: true });
      window.addEventListener("touchstart", unlockAudio, { once: true });
      this.preloadTick();
    }
  }

  // Crisp mechanical tactile click
  playClick() {
    this.playTick();
  }

  // Preload and decode official skiper-ui tick.wav
  private preloadTick() {
    if (this.isTickLoading || this.tickBuffer || typeof window === "undefined") return;
    this.isTickLoading = true;
    fetch("/sfx/tick.wav")
      .then((res) => {
        if (!res.ok) throw new Error("Local sfx fetch failed");
        return res.arrayBuffer();
      })
      .catch(() => {
        return fetch("https://skiper-ui.com/sfx/tick.wav").then((res) => res.arrayBuffer());
      })
      .then(async (arrayBuffer) => {
        const ctx = this.getContext();
        if (ctx) {
          this.tickBuffer = await ctx.decodeAudioData(arrayBuffer);
        }
      })
      .catch(() => {})
      .finally(() => {
        this.isTickLoading = false;
      });
  }

  // Authentic tactile "tik" sound matching skiper-ui.com/v1/skiper24
  playTick() {
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      if (this.tickBuffer) {
        const source = ctx.createBufferSource();
        source.buffer = this.tickBuffer;
        const gain = ctx.createGain();
        gain.gain.value = 0.75;
        source.connect(gain);
        gain.connect(ctx.destination);
        source.start(0);
        return;
      }

      // If AudioBuffer hasn't decoded yet, play HTML5 Audio
      const audio = new Audio("/sfx/tick.wav");
      audio.volume = 0.75;
      audio.play().catch(() => {});
    } catch {}
  }

  // Subtle metallic theme toggle switch
  playSwitch() {
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(740, now + 0.08);

      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.085);
    } catch {}
  }

  // Modern two-tone positive chime (copy command, connect repo)
  playSuccess() {
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;

      // Note 1
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = "sine";
      osc1.frequency.setValueAtTime(587.33, now); // D5
      gain1.gain.setValueAtTime(0.15, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.13);

      // Note 2
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = "sine";
      osc2.frequency.setValueAtTime(880, now + 0.07); // A5
      gain2.gain.setValueAtTime(0.2, now + 0.07);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.07);
      osc2.stop(now + 0.23);
    } catch {}
  }

  // Futuristic synth blip for sending prompt or running jobs
  playSend() {
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(1100, now + 0.1);

      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.11);
    } catch {}
  }
}

export const sounds = new SoundManager();
