// TextNode's native fast path compares text and raster size, but not locale.
// The font manager has already rebound the selected locale at this point.
// Rebuild the existing text texture once when its locale changes, including
// identical JP/CN labels and names. Preserve the native unchanged-frame path.
const guiRasterLocales = new Map();
Interceptor.attach(p(0x20739e), {onEnter() {
  const node = this.context.rdi.toString();
  const current = language();
  const previous = guiRasterLocales.get(node);
  guiRasterLocales.set(node, current);
  if (previous !== undefined && previous !== current) {
    this.context.r9 = ptr(1);
  }
}});
