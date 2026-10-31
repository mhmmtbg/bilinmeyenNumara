// Senaryo dosyalarını yükler. Sıra önemlidir: bir dosyanın son düğümü sıradakinin ilkine düşer.
import { parse, merge, validate } from './parser.js';

export const STORY_FILES = ['gun1.hikaye', 'gun2.hikaye', 'gun3.hikaye', 'gun4.hikaye', 'gun5.hikaye', 'sonlar.hikaye'];

export async function loadStory(base = 'hikaye/') {
  const parts = await Promise.all(STORY_FILES.map(async f => {
    const res = await fetch(base + f);
    if (!res.ok) throw new Error(`${f} yüklenemedi`);
    return parse(await res.text(), f);
  }));
  const story = merge(parts);
  const errors = validate(story);
  if (errors.length) console.warn('Senaryo uyarıları:\n' + errors.join('\n'));
  return story;
}
