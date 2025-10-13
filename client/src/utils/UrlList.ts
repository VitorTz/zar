import { Url } from "../model/Url";


let URLS: Url[] = []
const shortCodeSet = new Set()


export class UrlList {

    urls: Url[] = []

    constructor(urls: Url[]) {
        this.urls = urls
    }

    addMany(urls: Url[]): UrlList {
        urls.forEach(
            url => {
                if (!shortCodeSet.has(url.short_code)) {
                    URLS.unshift(url)
                    shortCodeSet.add(url.short_code)
                }
            }
        )
        return new UrlList(URLS)
    }

    add(url: Url): UrlList {
        if (!shortCodeSet.has(url.short_code)) {
            URLS.unshift(url)
            shortCodeSet.add(url.short_code)
        }
        return new UrlList(URLS)
    }

    remove(url: Url): UrlList {
        if (shortCodeSet.has(url.short_code)) {
            URLS = URLS.filter(i => i.short_code != url.short_code)
            shortCodeSet.delete(url.short_code)
        }
        return new UrlList(URLS)
    }

    favorite(url: Url, is_favorite: boolean): UrlList {
        if (shortCodeSet.has(url.short_code)) {
            URLS = URLS.map(i => i.short_code === url.short_code ? {...i, is_favorite} : i)
        }
        return new UrlList(URLS)
    }

    getUrls(): Url[] {
        return this.urls
    }    

}