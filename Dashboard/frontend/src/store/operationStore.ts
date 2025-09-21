import { create } from 'zustand';

export type Operation = 'venta' | 'renta';

interface OperationState {
  currentOperation: Operation;
  setOperation: (operation: Operation) => void;
}

export const useOperationStore = create<OperationState>((set) => ({
  currentOperation: 'venta',
  setOperation: (operation) => set({ currentOperation: operation }),
}));
