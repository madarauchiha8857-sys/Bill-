import { create } from 'zustand';

interface CartItem {
  product_id: string;
  name: string;
  price: number;
  image_base64?: string;
  quantity: number;
  stock: number;
}

interface CartState {
  items: CartItem[];
  total: number;
  setCart: (items: CartItem[], total: number) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartState>((set) => ({
  items: [],
  total: 0,
  setCart: (items, total) => set({ items, total }),
  clearCart: () => set({ items: [], total: 0 }),
}));
