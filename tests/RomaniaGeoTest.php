<?php

namespace Gabrieldev\RomaniaGeo\Tests;

use Gabrieldev\RomaniaGeo\RomaniaGeo;
use PHPUnit\Framework\TestCase;

class RomaniaGeoTest extends TestCase
{
    public function test_counties(): void
    {
        $this->assertCount(42, RomaniaGeo::counties());
        $this->assertSame('Iași', RomaniaGeo::county('is')['name']);
        $this->assertSame('BN', RomaniaGeo::county('Bistrita-Nasaud')['code']);
        $this->assertNull(RomaniaGeo::county('XX'));
    }

    public function test_localities_by_county(): void
    {
        foreach (RomaniaGeo::counties() as $county) {
            $this->assertCount($county['localities'], RomaniaGeo::localities($county['code']), $county['code']);
        }
        $this->assertCount(6, RomaniaGeo::localities('București'));
    }

    public function test_search_and_postal_codes(): void
    {
        $this->assertSame('Iași', RomaniaGeo::search('iasi')[0]['name']);
        $this->assertSame('Cluj-Napoca', RomaniaGeo::search('cluj', limit: 1)[0]['name']);
        $this->assertSame('București, Sectorul 1', RomaniaGeo::search('bucuresti')[0]['label']);

        $voluntari = RomaniaGeo::search('voluntari', 'IF')[0];
        $this->assertSame('077190', $voluntari['postal_code']);
        $this->assertSame('Voluntari', RomaniaGeo::byPostalCode(77190)[0]['name']);
        $this->assertSame('Voluntari', RomaniaGeo::locality($voluntari['siruta'])['name']);
    }

    public function test_normalize(): void
    {
        $this->assertSame('bistrita-nasaud', RomaniaGeo::normalize('  Bistrița-Năsăud '));
        $this->assertSame('tandarei', RomaniaGeo::normalize('Ţăndărei'));
        $this->assertFileExists(RomaniaGeo::path('romania.sql'));
    }
}
