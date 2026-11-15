// Small, dependency-free motion primitives shared across surfaces:
//  - usePrefersReducedMotion: live-tracks the OS accessibility setting.
//  - useReveal: IntersectionObserver-driven scroll reveal (returns a ref + flag).
//  - useCountUp: eased count-up for stat figures, gated on reduced-motion.
// All animation guards on reduced-motion so the portal stays calm when asked.

import { useEffect, useRef, useState } from 'react';

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState<boolean>(
    () => typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  );
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    if (!mq) return;
    const on = () => setReduced(mq.matches);
    mq.addEventListener?.('change', on);
    return () => mq.removeEventListener?.('change', on);
  }, []);
  return reduced;
}

/**
 * Reveal an element the first time it scrolls into view. Returns a ref to
 * attach and a `visible` flag; compose with the `.reveal` / `.is-visible` CSS
 * (see index.css). Falls back to visible when IntersectionObserver is absent.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(rootMargin = '0px 0px -12% 0px') {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!('IntersectionObserver' in window)) {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setVisible(true);
            io.unobserve(e.target);
          }
        }
      },
      { rootMargin, threshold: 0.12 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [rootMargin]);
  return { ref, visible };
}

/**
 * Ease a number from 0 up to `target` once `active` is true. Snaps instantly
 * for reduced-motion or a null target. Great for hero stat figures.
 */
export function useCountUp(target: number | null, active = true, duration = 1150): number {
  const reduced = usePrefersReducedMotion();
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target == null) {
      setValue(0);
      return;
    }
    if (reduced || !active) {
      setValue(target);
      return;
    }
    // Compliance-co fix (17 Aug 2026): this used to Math.round() every animated
    // frame unconditionally, which is right for a whole-number counter (a
    // document count) but silently mangles any DECIMAL stat (a 4.7 average
    // REMi score animates to Math.round(4.7) = 5, then the caller's own
    // format={(v) => v.toFixed(1)} just prints the now-wrong "5.0" — the KB-
    // verified number on screen was never the number actually computed). Only
    // round intermediate frames to a whole number when the TARGET itself is
    // a whole number, so integer counters keep their crisp non-decimal
    // count-up and fractional stats animate — and land on — their real value.
    const isInt = Number.isInteger(target);
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const v = target * eased;
      setValue(isInt ? Math.round(v) : v);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, reduced, duration]);
  return value;
}
