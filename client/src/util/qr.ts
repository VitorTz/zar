// qr.ts
import QRCode from "qrcode";

/**
 * Gera um dataURL PNG do QR code para a url fornecida.
 * @param url string - a URL que será codificada
 * @param size number - largura/altura em pixels (opcional)
 * @returns Promise<string> - dataURL PNG
 */
export async function generateQrDataUrl(url: string, size = 300): Promise<string> {
  if (!url) throw new Error("URL required");
  // opções: margem pequena, largura definida
  const opts: QRCode.QRCodeToDataURLOptions = { margin: 1, width: size };
  return QRCode.toDataURL(url, opts);
}

/**
 * Alternativa: desenha em um <canvas> e retorna o dataURL.
 */
export async function generateQrOnCanvas(canvas: HTMLCanvasElement, url: string, size = 300): Promise<string> {
  canvas.width = size;
  canvas.height = size;
  await QRCode.toCanvas(canvas, url, { margin: 1, width: size });
  return canvas.toDataURL("image/png");
}