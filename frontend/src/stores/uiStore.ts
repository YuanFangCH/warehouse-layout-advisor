import { create } from 'zustand';

interface UIState {
  mobileNavOpen: boolean;
  conditionModalOpen: boolean;
  selectedEvidenceId: string | null;
  lastError: string | null;
  toggleMobileNav: () => void;
  setConditionModalOpen: (open: boolean) => void;
  setSelectedEvidenceId: (id: string | null) => void;
  setLastError: (message: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  mobileNavOpen: false,
  conditionModalOpen: false,
  selectedEvidenceId: null,
  lastError: null,
  toggleMobileNav: () => set((state) => ({ mobileNavOpen: !state.mobileNavOpen })),
  setConditionModalOpen: (open) => set({ conditionModalOpen: open }),
  setSelectedEvidenceId: (id) => set({ selectedEvidenceId: id }),
  setLastError: (message) => set({ lastError: message }),
}));
