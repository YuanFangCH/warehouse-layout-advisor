import { X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import { useUIStore } from '../stores/uiStore';

export default function ErrorBanner() {
  const lastError = useUIStore((state) => state.lastError);
  const setLastError = useUIStore((state) => state.setLastError);

  return (
    <AnimatePresence>
      {lastError ? (
        <motion.div
          className="error-banner"
          role="alert"
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          exit="hidden"
        >
          <span>{lastError}</span>
          <button type="button" onClick={() => setLastError(null)} aria-label="关闭错误提示">
            <X size={14} />
          </button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
