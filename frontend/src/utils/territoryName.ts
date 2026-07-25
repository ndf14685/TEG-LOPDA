const CONTINENT_PREFIXES = [
  'south-america-', 'north-america-', 'europe-', 'africa-', 'asia-', 'oceania-',
];

/** "territory-south-america-colombia" → "colombia" (la UI capitaliza con CSS). */
export function territoryName(id: string): string {
  let rest = id.replace(/^territory-/, '');
  for (const prefix of CONTINENT_PREFIXES) {
    if (rest.startsWith(prefix)) {
      rest = rest.slice(prefix.length);
      break;
    }
  }
  return rest.replaceAll('-', ' ');
}
