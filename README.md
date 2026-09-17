# HRA renovasjon for Home Assistant

En HACS-kompatibel custom integration for HRA (Hadeland og Ringerike Avfallsselskap). Integrasjonen bruker HRA sitt offentlige API, søker opp adressen og henter kommende hentedager for valgt renovasjonsavtale.

## Funksjoner

- Konfigureres fra **Settings → Devices & services → Add integration**.
- Søk på adresse, med valg av riktig eiendom dersom HRA gir flere treff.
- Én datumsensor per avfallsfraksjon som HRA returnerer.
- En samlet sensor `HRA neste henting` med neste dato, fraksjon, dager igjen og kommende hentedager som attributter.
- En binærsensor `HRA hentedag` som er `on` når minst én fraksjon hentes i dag, med attributtene `rest`, `mat`, `papir`, `glass` og `plast` for neste henting.
- En kalender med heldagshendelser for alle kommende hentedager.
- HRA-symboler som lokale bilder på fraksjonssensorene. Papir/kartong og glass/metall vises som to originale HRA-symboler side ved side.
- HRA-logo som integrasjonsikon og logo i Home Assistant.
- Oppdateringsintervall fra 1 til 168 timer, standard 24 timer.

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
