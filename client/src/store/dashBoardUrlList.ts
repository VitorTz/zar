import { create } from "zustand";
import { UrlList } from "../utils/UrlList";


interface UrlState {
    urlList: UrlList,
    setUrlList: (urlList: UrlList) => any
}


export const useDashboardUrlList = create<UrlState>((set) => ({
    urlList: new UrlList(),  
    setUrlList: (urlList: UrlList) => set((state) => ({ urlList }))
}));