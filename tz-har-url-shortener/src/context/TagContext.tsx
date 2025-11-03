import { createContext, useContext, useState, type ReactNode } from "react";
import type { UrlTag } from "../types/URL";


interface UrlTagContextType {
  tags: UrlTag[];
  setTags: (tags: UrlTag[]) => void;
  addTag: (tag: UrlTag) => void;
  removeTag: (id: number) => void;
  clearTags: () => void;
}


const UrlTagContext = createContext<UrlTagContextType | undefined>(undefined);

export const UrlTagProvider = ({ children }: { children: ReactNode }) => {
  const [tags, setTags] = useState<UrlTag[]>([]);

  const addTag = (tag: UrlTag) => setTags((prev) => [...prev, tag]);

  const removeTag = (id: number) =>
    setTags((prev) => prev.filter((t) => t.id !== id));

  const clearTags = () => setTags([]);

  return (
    <UrlTagContext.Provider value={{ tags, setTags, addTag, removeTag, clearTags }}>
      {children}
    </UrlTagContext.Provider>
  );
};

export const useUrlTags = (): UrlTagContextType => {
  const context = useContext(UrlTagContext);
  if (!context) throw new Error("useUrlTags must be used within a UrlTagProvider");
  return context;
};