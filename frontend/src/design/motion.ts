import type { Transition, Variants } from 'motion/react';

type Bezier = [number, number, number, number];

export const DURATIONS = {
  press: 0.12,
  popover: 0.18,
  modal: 0.22,
  drawer: 0.26,
  panel: 0.24,
} as const;

export const EASE_OUT: Bezier = [0.23, 1, 0.32, 1];
export const EASE_IN_OUT: Bezier = [0.65, 0, 0.35, 1];
export const EASE_PRESS: Bezier = [0.32, 0, 0.67, 0];

export const STAGGER_DELAY = 0.04;

const panelTransition: Transition = {
  duration: DURATIONS.panel,
  ease: EASE_OUT,
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: (index: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      ...panelTransition,
      delay: index * STAGGER_DELAY,
    },
  }),
};

export const popIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: DURATIONS.modal,
      ease: EASE_OUT,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.97,
    transition: {
      duration: DURATIONS.modal * 0.75,
      ease: EASE_IN_OUT,
    },
  },
};

export const fade: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      duration: DURATIONS.popover,
      ease: EASE_OUT,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: DURATIONS.popover * 0.75,
      ease: EASE_IN_OUT,
    },
  },
};

export const drawer: Variants = {
  closed: {
    x: '-100%',
    transition: {
      type: 'spring',
      stiffness: 420,
      damping: 40,
    },
  },
  open: {
    x: 0,
    transition: {
      type: 'spring',
      stiffness: 420,
      damping: 40,
    },
  },
};

export const expand: Variants = {
  hidden: { opacity: 0, height: 0 },
  visible: {
    opacity: 1,
    height: 'auto',
    transition: {
      duration: DURATIONS.panel,
      ease: EASE_IN_OUT,
    },
  },
  exit: {
    opacity: 0,
    height: 0,
    transition: {
      duration: DURATIONS.popover,
      ease: EASE_IN_OUT,
    },
  },
};
