import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';

import { fade, popIn } from '../design/motion';

interface ModalProps {
  open: boolean;
  title: string;
  eyebrow?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export default function Modal({ open, title, eyebrow, onClose, children, footer }: ModalProps) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          variants={fade}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={onClose}
        >
          <motion.div
            className="modal"
            variants={popIn}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
                <h2>{title}</h2>
              </div>
              <button className="icon-button" type="button" onClick={onClose} aria-label="关闭">
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">{children}</div>
            {footer ? <div className="modal-actions">{footer}</div> : null}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
