import { create } from "zustand";
import { Url } from "../model/Url";


interface UrlState {
    urls: Url[]  
    setUrls: (urls: Url[]) => any
    favoriteUrl: (url: Url) => any
    deleteUrl: (url: Url) => any
}


export const useUrlListState = create<UrlState>((set) => ({
    urls: [],  
    setUrls: (urls: Url[]) => set((state) => ({ urls })),
    deleteUrl: (url: Url) => set((state) => ({urls: state.urls.filter(i => i.id != url.id)})),
    favoriteUrl: (url: Url) => set((state) => ({
        urls: state.urls.map(i => i.id == url.id ? {...i, is_favorite: !i.is_favorite} : i)
    }))
}));