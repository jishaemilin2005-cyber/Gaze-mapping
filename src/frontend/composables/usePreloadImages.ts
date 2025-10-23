// src/frontend/composables/usePreloadImages.ts
export function usePreloadImages(urls: string[]) {
  const cache = new Map<string, Promise<HTMLImageElement>>();

  const preload = (url: string) => {
    if (!cache.has(url)) {
      cache.set(url, new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = url;
      }));
    }
    return cache.get(url)!;
  };

  const preloadAll = async () => Promise.all(urls.map(preload));

  return { preload, preloadAll };
}
