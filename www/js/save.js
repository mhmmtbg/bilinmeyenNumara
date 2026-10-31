// Kayıt: oyun durumu ve ayarlar localStorage'da.
import { SAVE_VERSION } from './engine.js';

const KEY = 'bn_kayit_v1';
const PREF = 'bn_ayar_v1';

export function loadGame() {
  try {
    const st = JSON.parse(localStorage.getItem(KEY));
    return st && st.v === SAVE_VERSION ? st : null;
  } catch { return null; }
}
export function saveGame(st) {
  try { localStorage.setItem(KEY, JSON.stringify(st)); } catch {}
}
export function clearGame() {
  try { localStorage.removeItem(KEY); } catch {}
}

const DEFAULT_PREFS = { theme: 'dark', size: 1, speed: 1 };
export function loadPrefs() {
  try { return { ...DEFAULT_PREFS, ...JSON.parse(localStorage.getItem(PREF)) }; } catch { return { ...DEFAULT_PREFS }; }
}
export function savePrefs(p) {
  try { localStorage.setItem(PREF, JSON.stringify(p)); } catch {}
}
