/** Presentation catalogs for the Artist Space profile form (051). */

export interface CatalogOption {
  readonly value: string;
  readonly label: string;
}

/** ISO 3166-1 alpha-2 subset covering the product's active markets. */
export const ARTIST_COUNTRY_CATALOG: readonly CatalogOption[] = [
  { value: 'EC', label: 'Ecuador' },
  { value: 'MX', label: 'México' },
  { value: 'CO', label: 'Colombia' },
  { value: 'PE', label: 'Perú' },
  { value: 'CL', label: 'Chile' },
  { value: 'AR', label: 'Argentina' },
  { value: 'BR', label: 'Brasil' },
  { value: 'UY', label: 'Uruguay' },
  { value: 'PY', label: 'Paraguay' },
  { value: 'BO', label: 'Bolivia' },
  { value: 'VE', label: 'Venezuela' },
  { value: 'CR', label: 'Costa Rica' },
  { value: 'PA', label: 'Panamá' },
  { value: 'DO', label: 'República Dominicana' },
  { value: 'PR', label: 'Puerto Rico' },
  { value: 'ES', label: 'España' },
  { value: 'US', label: 'Estados Unidos' },
  { value: 'CA', label: 'Canadá' },
  { value: 'GB', label: 'Reino Unido' },
  { value: 'FR', label: 'Francia' },
  { value: 'DE', label: 'Alemania' },
  { value: 'IT', label: 'Italia' },
  { value: 'PT', label: 'Portugal' },
];

/** Genre codes stored verbatim on the profile; labels stay presentation-only. */
export const ARTIST_GENRE_CATALOG: readonly CatalogOption[] = [
  { value: 'latin', label: 'Latino' },
  { value: 'pop', label: 'Pop' },
  { value: 'rock', label: 'Rock' },
  { value: 'urbano', label: 'Urbano / Reguetón' },
  { value: 'hip_hop', label: 'Hip hop' },
  { value: 'electronic', label: 'Electrónica' },
  { value: 'jazz', label: 'Jazz' },
  { value: 'classical', label: 'Clásica' },
  { value: 'folk', label: 'Folclore' },
  { value: 'cumbia', label: 'Cumbia' },
  { value: 'salsa', label: 'Salsa' },
  { value: 'bachata', label: 'Bachata' },
  { value: 'rnb', label: 'R&B / Soul' },
  { value: 'metal', label: 'Metal' },
  { value: 'indie', label: 'Indie / Alternativo' },
  { value: 'other', label: 'Otro' },
];

/** External identifier systems the platform links against. */
export const ARTIST_IDENTIFIER_SYSTEMS: readonly CatalogOption[] = [
  { value: 'spotify', label: 'Spotify' },
  { value: 'apple_music', label: 'Apple Music' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'deezer', label: 'Deezer' },
  { value: 'audius', label: 'Audius' },
  { value: 'isni', label: 'ISNI' },
  { value: 'ipi', label: 'IPI' },
];
