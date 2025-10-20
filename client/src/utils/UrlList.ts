import { URLResponse } from "../model/Url"

let urls: URLResponse[] = []    
let shortCodeSet = new Set()


export class UrlList {
    
    addMany(newUrls: URLResponse[]): UrlList {
        newUrls.forEach(url => {
            if (!shortCodeSet.has(url.short_code)) {
                shortCodeSet.add(url.short_code)
                urls.unshift(url)
            }
        })
        return new UrlList()
    }

    add(url: URLResponse): UrlList {
        if (!shortCodeSet.has(url.short_code)) {
            shortCodeSet.add(url.short_code)
            urls.unshift(url)
        }
        return new UrlList()
    }

    set(newUrls: URLResponse[]): UrlList {
        urls = newUrls
        shortCodeSet = new Set(newUrls.map(i => i.short_code))
        return new UrlList()
    }

    remove(url: URLResponse): UrlList {
        if (shortCodeSet.has(url.short_code)) {
            shortCodeSet.delete(url.short_code)
            urls = urls.filter(i => i.short_code != url.short_code)
        }
        return new UrlList()
    }

    favorite(url: URLResponse, is_favorite: boolean): UrlList {
        if (shortCodeSet.has(url.short_code)) {
            urls = urls.map(i => i.short_code === url.short_code ? {...i, is_favorite} : i)
        }
        return new UrlList()
    }

    getUrls(): URLResponse[] {
        return urls
    }    

    isEmpty() {
        return urls.length === 0
    }

}