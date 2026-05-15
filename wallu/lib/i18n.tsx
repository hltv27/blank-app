'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import en from '@/messages/en.json';
import pt from '@/messages/pt.json';
import es from '@/messages/es.json';
import fr from '@/messages/fr.json';
import de from '@/messages/de.json';
import zh from '@/messages/zh.json';
import hi from '@/messages/hi.json';
import ar from '@/messages/ar.json';
import ru from '@/messages/ru.json';
import ja from '@/messages/ja.json';

export type Lang = 'en' | 'pt' | 'es' | 'fr' | 'de' | 'zh' | 'hi' | 'ar' | 'ru' | 'ja';

export const LANGUAGES: { code: Lang; label: string; flag: string; dir?: 'rtl' }[] = [
  { code: 'en', label: 'English',    flag: '🇬🇧' },
  { code: 'pt', label: 'Português',  flag: '🇵🇹' },
  { code: 'es', label: 'Español',    flag: '🇪🇸' },
  { code: 'fr', label: 'Français',   flag: '🇫🇷' },
  { code: 'de', label: 'Deutsch',    flag: '🇩🇪' },
  { code: 'zh', label: '中文',        flag: '🇨🇳' },
  { code: 'hi', label: 'हिन्दी',     flag: '🇮🇳' },
  { code: 'ar', label: 'العربية',    flag: '🇸🇦', dir: 'rtl' },
  { code: 'ru', label: 'Русский',    flag: '🇷🇺' },
  { code: 'ja', label: '日本語',      flag: '🇯🇵' },
];

type Messages = Record<string, string>;
type TFunc = (key: string, vars?: Record<string, string | number>) => string;

const LANG_KEY = 'wallu_lang';
const allMessages: Record<Lang, any> = { en, pt, es, fr, de, zh, hi, ar, ru, ja };

function flatten(obj: Record<string, any>, prefix = ''): Messages {
  return Object.entries(obj).reduce((acc, [k, v]) => {
    const key = prefix ? `${prefix}.${k}` : k;
    if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
      Object.assign(acc, flatten(v, key));
    } else {
      acc[key] = String(v);
    }
    return acc;
  }, {} as Messages);
}

const flatMessages: Record<Lang, Messages> = Object.fromEntries(
  Object.entries(allMessages).map(([lang, msgs]) => [lang, flatten(msgs)])
) as Record<Lang, Messages>;

const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: TFunc }>({
  lang: 'en', setLang: () => {}, t: (key) => key,
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>('en');

  useEffect(() => {
    const stored = localStorage.getItem(LANG_KEY) as Lang | null;
    if (stored && flatMessages[stored]) setLangState(stored);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = LANGUAGES.find(l => l.code === lang)?.dir === 'rtl' ? 'rtl' : 'ltr';
  }, [lang]);

  const setLang = (l: Lang) => { setLangState(l); localStorage.setItem(LANG_KEY, l); };

  const t: TFunc = (key, vars) => {
    let str = flatMessages[lang]?.[key] ?? flatMessages.en[key] ?? key;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) str = str.replaceAll(`{{${k}}}`, String(v));
    }
    return str;
  };

  return <LangContext.Provider value={{ lang, setLang, t }}>{children}</LangContext.Provider>;
}

export const useLang = () => useContext(LangContext);
export const useT = () => useContext(LangContext).t;
