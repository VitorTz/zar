

function wrapText(context: any, text: string, x: number, y: number, maxWidth: number, lineHeight: number) {
  const words = text.split(' ');
  let line = '';

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = context.measureText(testLine);
    const testWidth = metrics.width;
    if (testWidth > maxWidth && n > 0) {
      context.fillText(line, x, y);
      line = words[n] + ' ';
      y += lineHeight;
    } else {
      line = testLine;
    }
  }
  context.fillText(line, x, y);
}


export async function generateUrlImage({ 
  qrCodeUrl, 
  title, 
  description, 
  originalUrl, 
  shortUrl 
}: {qrCodeUrl: string, title: string, description: string, originalUrl: string, shortUrl: string}) {
  const canvas = document.createElement('canvas');
  const width = 800;
  const height = 1000;
  canvas.width = width;
  canvas.height = height;
  const ctx: CanvasRenderingContext2D = canvas.getContext('2d')!;
  
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, width, height);
  
  const qrImage = new Image();
  qrImage.crossOrigin = 'anonymous';
  qrImage.src = qrCodeUrl;
  await new Promise((resolve) => { qrImage.onload = resolve; });
  
  const qrSize = 400;
  const qrX = (width - qrSize) / 2;
  const qrY = 100;
  ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);

  ctx.textAlign = 'center';

  // Título
  ctx.fillStyle = '#1a1a1a';
  ctx.font = 'bold 52px Poppins, sans-serif';
  ctx.fillText(title, width / 2, qrY + qrSize + 80);

  // Descrição
  ctx.fillStyle = '#6b7280';
  ctx.font = '32px Poppins, sans-serif';
  wrapText(ctx, description, width / 2, qrY + qrSize + 150, width - 100, 40);

  ctx.fillStyle = '#6b7280';
  ctx.font = '24px Poppins, sans-serif';
  const maxOriginalUrlWidth = width - 100;
  let truncatedOriginalUrl = originalUrl;
  if (ctx.measureText(originalUrl).width > maxOriginalUrlWidth) {
      while (ctx.measureText(truncatedOriginalUrl + '...').width > maxOriginalUrlWidth) {
          truncatedOriginalUrl = truncatedOriginalUrl.slice(0, -1);
      }
      truncatedOriginalUrl += '...';
  }
  ctx.fillText(truncatedOriginalUrl, width / 2, height - 120);  
  
  return canvas.toDataURL('image/png');
}