/**
 * Compresses an image file client-side before upload.
 * Scales so the LARGER dimension (width or height) fits within maxDimension —
 * this matters because vision-model token cost scales with pixel count,
 * not just width. Never upscales. Re-encodes as JPEG at the given quality.
 */
export const compressImage = (file, maxDimension = 600, quality = 0.5) => {
  if (!file || !file.type.startsWith('image/')) {
    return Promise.reject(new Error('File is not an image'));
  }

  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const largerDim = Math.max(img.width, img.height);
        const scale = Math.min(maxDimension / largerDim, 1);

        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(
          (blob) => {
            URL.revokeObjectURL(objectUrl);
            if (!blob) {
              reject(new Error('Canvas to Blob conversion failed'));
              return;
            }
            const compressedFile = new File(
              [blob],
              file.name.replace(/\.[^/.]+$/, '.jpg'),
              { type: 'image/jpeg', lastModified: Date.now() }
            );
            resolve(compressedFile);
          },
          'image/jpeg',
          quality
        );
      } catch (err) {
        URL.revokeObjectURL(objectUrl);
        reject(err);
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('Failed to load image for compression'));
    };

    img.src = objectUrl;
  });
};