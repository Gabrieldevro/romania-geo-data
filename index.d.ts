export type LocalityType = 'municipiu' | 'oraș' | 'sector' | 'localitate componentă' | 'sat';

export interface County {
  /** Car plate code: "AB", "IS", "B" */
  code: string;
  name: string;
  siruta: number;
  region: string;
  seat: string | null;
  localities: number;
}

export interface Locality {
  siruta: number;
  name: string;
  /** Disambiguated name for dropdowns: "Valea Mare (com. Priboieni)" */
  label: string;
  county: string;
  type: LocalityType;
  urban: boolean;
  uat_siruta: number;
  uat_name: string | null;
  uat_type: 'municipiu' | 'oraș' | 'comună' | null;
  /** Single postal code, or null for cities that have one code per street */
  postal_code: string | null;
  street_level_postal_codes: boolean;
}

export function normalize(text: string): string;
export function counties(): County[];
export function county(codeOrName: string): County | null;
export function localities(countyCodeOrName?: string): Locality[];
export function locality(siruta: number | string): Locality | null;
export function search(query: string, options?: { county?: string; limit?: number }): Locality[];
export function byPostalCode(code: string | number): Locality[];

declare const _default: {
  normalize: typeof normalize;
  counties: typeof counties;
  county: typeof county;
  localities: typeof localities;
  locality: typeof locality;
  search: typeof search;
  byPostalCode: typeof byPostalCode;
};
export default _default;
