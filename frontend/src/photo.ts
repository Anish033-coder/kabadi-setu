// Canvas exports new pixels and drops EXIF, including GPS. No original file is uploaded.
export async function preparePhoto(file: File): Promise<Blob> {
  if (file.size > 20 * 1024 * 1024)
    throw new Error("Choose a photo smaller than 20 MB.");
  const bitmap = await createImageBitmap(file, {
    imageOrientation: "from-image",
  });
  try {
    const ratio = Math.min(1, 1024 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * ratio));
    canvas.height = Math.max(1, Math.round(bitmap.height * ratio));
    const context = canvas.getContext("2d");
    if (!context)
      throw new Error("Photo preparation is unavailable. Use manual search.");
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(
        (value) =>
          value
            ? resolve(value)
            : reject(new Error("Could not prepare this photo.")),
        "image/jpeg",
        0.8,
      ),
    );
    if (blob.size > 2 * 1024 * 1024)
      throw new Error("Photo is too large. Try a closer crop.");
    return blob;
  } finally {
    bitmap.close();
  }
}
