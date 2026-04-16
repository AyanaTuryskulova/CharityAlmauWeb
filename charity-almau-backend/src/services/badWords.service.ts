const BAD_WORDS_RU = [
  'блять', 'бля', 'блядь', 'сука', 'сучка', 'хуй', 'хуя', 'хуе', 'хуё',
  'пизда', 'пизд', 'ебать', 'ебан', 'ёбан', 'еба', 'ёба', 'ебу', 'ебл',
  'ёбл', 'нахуй', 'нахуя', 'пиздец', 'залупа', 'мудак', 'мудил', 'дрочи',
  'пидор', 'пидар', 'гандон', 'шлюха', 'долбо', 'дебил', 'уебок', 'уёбок',
  'уебан', 'уёбан', 'выебан', 'заебал', 'заёбал', 'отъеб', 'съеби', 'ебис',
  'хуес', 'хуёв', 'пиздат', 'пиздос', 'ёбтвою', 'ебтвою', 'ёпт', 'епт',
];

const BAD_WORDS_KZ = [
  'сиқтыр', 'сиктир', 'көтақ', 'котак', 'жынды', 'сасық', 'құтақ',
  'кутак', 'момын', 'қотақ', 'тақия',
];

const BAD_WORDS_EN = [
  'fuck', 'shit', 'bitch', 'asshole', 'dick', 'pussy', 'cunt', 'cock',
  'bastard', 'slut', 'whore', 'nigger', 'faggot', 'retard', 'motherfuck',
  'bullshit', 'dumbass', 'jackass', 'dipshit',
];

const ALL_BAD_WORDS = [...BAD_WORDS_RU, ...BAD_WORDS_KZ, ...BAD_WORDS_EN];

// Normalize: replace common substitutions
function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/@/g, 'a')
    .replace(/0/g, 'o')
    .replace(/3/g, 'e')
    .replace(/\$/g, 's')
    .replace(/1/g, 'i')
    .replace(/[^a-zа-яёәғқңөұүһі\s]/g, '');
}

export function containsBadWords(text: string): boolean {
  const normalized = normalize(text);
  return ALL_BAD_WORDS.some((word) => normalized.includes(word));
}

export function checkTexts(...texts: (string | null | undefined)[]): boolean {
  return texts.some((t) => t && containsBadWords(t));
}
