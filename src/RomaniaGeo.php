<?php

namespace Gabrieldev\RomaniaGeo;

/**
 * Romanian counties and localities (INS SIRUTA + Poșta Română postal codes).
 *
 *   RomaniaGeo::county('IS')['name'];          // "Iași"
 *   RomaniaGeo::localities('B');                // the 6 sectors
 *   RomaniaGeo::search('valea mare', 'AB');
 */
final class RomaniaGeo
{
    /** @var list<array<string, mixed>>|null */
    private static ?array $counties = null;

    /** @var list<array<string, mixed>>|null */
    private static ?array $localities = null;

    public static function normalize(?string $text): string
    {
        $text = (string) $text;
        $text = strtr($text, [
            'ă' => 'a', 'â' => 'a', 'î' => 'i', 'ș' => 's', 'ş' => 's', 'ț' => 't', 'ţ' => 't',
            'Ă' => 'a', 'Â' => 'a', 'Î' => 'i', 'Ș' => 's', 'Ş' => 's', 'Ț' => 't', 'Ţ' => 't',
        ]);

        return trim(preg_replace('/\s+/', ' ', mb_strtolower($text)) ?? '');
    }

    /** @return list<array<string, mixed>> */
    public static function counties(): array
    {
        return self::$counties ??= self::load('counties.json');
    }

    /** @return array<string, mixed>|null */
    public static function county(string $codeOrName): ?array
    {
        $key = self::normalize($codeOrName);
        foreach (self::counties() as $county) {
            if (strtolower($county['code']) === $key || self::normalize($county['name']) === $key) {
                return $county;
            }
        }

        return null;
    }

    /** @return list<array<string, mixed>> */
    public static function localities(?string $county = null): array
    {
        $all = self::$localities ??= self::load('localities.json');
        if ($county === null) {
            return $all;
        }
        $code = self::county($county)['code'] ?? null;

        return $code === null ? [] : array_values(array_filter($all, fn ($l) => $l['county'] === $code));
    }

    /** @return array<string, mixed>|null */
    public static function locality(int|string $siruta): ?array
    {
        foreach (self::localities() as $locality) {
            if ($locality['siruta'] === (int) $siruta) {
                return $locality;
            }
        }

        return null;
    }

    /**
     * Diacritic- and case-insensitive: exact names first, then prefixes, then substrings; towns before villages.
     *
     * @return list<array<string, mixed>>
     */
    public static function search(string $query, ?string $county = null, int $limit = 20): array
    {
        $q = self::normalize($query);
        if ($q === '') {
            return [];
        }
        $rank = ['municipiu' => 0, 'oraș' => 1, 'sector' => 1, 'localitate componentă' => 3, 'sat' => 4];

        $hits = [];
        foreach (self::localities($county) as $locality) {
            $name = self::normalize($locality['name']);
            $label = self::normalize($locality['label']);
            $score = $name === $q ? 0 : (str_starts_with($name, $q) || str_starts_with($label, $q) ? 1 : (str_contains($label, $q) ? 2 : -1));
            if ($score >= 0) {
                $hits[] = [$score, $rank[$locality['type']] ?? 5, $name, $locality];
            }
        }
        usort($hits, fn ($a, $b) => [$a[0], $a[1], $a[2]] <=> [$b[0], $b[1], $b[2]]);

        return array_column(array_slice($hits, 0, $limit), 3);
    }

    /** @return list<array<string, mixed>> */
    public static function byPostalCode(string|int $code): array
    {
        $code = str_pad(trim((string) $code), 6, '0', STR_PAD_LEFT);

        return array_values(array_filter(self::localities(), fn ($l) => $l['postal_code'] === $code));
    }

    /** Path to a bundled data file, e.g. for your own seeder: RomaniaGeo::path('romania.sql'). */
    public static function path(string $file): string
    {
        return dirname(__DIR__).'/data/'.$file;
    }

    /** @return list<array<string, mixed>> */
    private static function load(string $file): array
    {
        return json_decode((string) file_get_contents(self::path($file)), true, flags: JSON_THROW_ON_ERROR);
    }
}
