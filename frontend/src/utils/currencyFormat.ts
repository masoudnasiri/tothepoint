export type CurrencyCode = string;

const SYMBOLS: Record<string, string> = {
  IRR: 'ریال',
  USD: '$',
  EUR: '€',
  AED: 'د.إ',
  CNY: '¥',
  TRY: '₺',
  GBP: '£',
  JPY: '¥',
};

const PERSIAN_LABELS: Record<string, string> = {
  IRR: 'ریال',
  USD: 'دلار',
  EUR: 'یورو',
  AED: 'درهم',
  CNY: 'یوان',
  TRY: 'لیر',
  GBP: 'پوند',
  JPY: 'ین',
};

export function getCurrencySymbol(currency: CurrencyCode | null | undefined): string {
  const code = (currency || 'IRR').trim().toUpperCase();
  return SYMBOLS[code] || code;
}

export function formatCurrencyAmount(
  amount: number | string | null | undefined,
  currency: CurrencyCode | null | undefined,
  locale: string = 'en-US'
): string {
  const value = typeof amount === 'string' ? Number(amount) : amount ?? 0;
  const safeValue = Number.isFinite(value) ? Number(value) : 0;
  const code = (currency || 'IRR').trim().toUpperCase();
  const isRial = code === 'IRR';
  const useFa = locale.startsWith('fa');
  const fractionDigits = isRial ? 0 : 2;
  const formattedNumber = safeValue.toLocaleString(useFa ? 'fa-IR' : locale, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });

  if (useFa) {
    const label = PERSIAN_LABELS[code] || code;
    return `${formattedNumber} ${label}`;
  }

  const symbol = getCurrencySymbol(code);
  if (code === 'IRR') {
    return `${formattedNumber} ${symbol}`;
  }
  if (symbol.length <= 2 || symbol === 'د.إ') {
    return `${symbol}${formattedNumber}`;
  }
  return `${formattedNumber} ${symbol}`;
}

