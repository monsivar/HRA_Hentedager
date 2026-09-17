# HRA renovasjon for Home Assistant

En HACS-kompatibel custom integration for HRA (Hadeland og Ringerike Avfallsselskap). Integrasjonen bruker HRA sitt offentlige API, søker opp adressen og henter kommende hentedager for valgt renovasjonsavtale.

## Funksjoner

- Konfigureres fra **Settings → Devices & services → Add integration**.
- Søk på adresse, med valg av riktig eiendom dersom HRA gir flere treff.
- Én datumsensor per avfallsfraksjon som HRA returnerer.
- En samlet sensor `HRA neste henting` med neste dato, fraksjon, dager igjen og kommende hentedager som attributter.
- En binærsensor `HRA hentedag` som er `on` når minst én fraksjon hentes i dag, med attributtene `rest`, `mat`, `papir`, `glass` og `plast` for neste henting.
- En kalender med heldagshendelser for alle kommende hentedager.
- Kalenderhendelser får en beskrivende emoji foran avfallstypen.
- Entitetene organiseres i Home Assistant som to logiske enheter: fraksjons-/datosensorene samles separat fra binærsensoren og kalenderen.
- HRA-symboler som lokale bilder på fraksjonssensorene. Papir/kartong og glass/metall vises som to originale HRA-symboler side ved side.
- HRA-logo som integrasjonsikon og logo i Home Assistant.
- Oppdateringsintervall fra 1 til 168 timer, standard 24 timer.

## HRA-kort

Integrasjonen inneholder et Mushroom-inspirert Lovelace-kort som grupperer flere avfallstyper når de har samme hentedato. Kortet bruker sammendragssensorens `upcoming`-attributt og viser neste henting samt de neste datoene.

Kortet registreres automatisk av integrasjonen og kan legges til uten manuell dashboard-ressurs:

```yaml
type: custom:hra-renovasjon-card
max_dates: 4
```

Når det bare finnes én HRA-avtale, finner kortet selv riktig sammendragssensor og kalender. Ved flere avtaler kan de velges i Home Assistants visuelle kortredigering, eller angis eksplisitt:

```yaml
type: custom:hra-renovasjon-card
entity: sensor.hra_neste_henting
calendar: calendar.hra_hentedager
max_dates: 4
```

## Installasjon

1. Legg dette repositoryet til i HACS som et custom repository av typen **Integration**.
2. Installer **HRA renovasjon**.
3. Start Home Assistant på nytt.
4. Legg til integrasjonen fra **Settings → Devices & services**.

Manuell installasjon: kopier mappen `custom_components/hra_renovasjon` til Home Assistant sin `config/custom_components`-mappe.

## API

Integrasjonen bruker HRA-endepunktene:

- `GET https://api.hra.no/search/address?query=...`
- `GET https://api.hra.no/Renovation/UpcomingGarbageDisposals/{agreementGuid}`

API-et kan endres av HRA uten varsel. Integrasjonen er ikke offisielt tilknyttet HRA.

## Bilder

Bildene i `custom_components/hra_renovasjon/assets` er hentet fra HRA sine offentlige bildeadresser. De seks originale symbolene beholdes uendret. De kombinerte fraksjonene bruker lokale kvadratiske PNG-filer med heldekkende bakgrunn og de to originale symbolene side ved side, med lik luft rundt symbolene.

## Ansvarsfraskrivelse

Dette er et uavhengig og uoffisielt prosjekt, og integrasjonen har ingen tilknytning til eller godkjenning fra Hadeland og Ringerike Avfallsselskap (HRA). Den er laget for å gjøre hverdagen litt enklere for mennesker som bor på Ringerike og Hadeland.
