---
tittel: "Hva er MTA-STS og TLS-RPT? En praktisk forklaring"
metabeskrivelse: "Hva er MTA-STS, og hvorfor trenger du TLS-RPT? Slik setter du opp policyfilen og _mta-sts-posten, og går trygt fra testing til enforce."
målsøk:
  - "hva er MTA-STS"
  - "TLS-RPT"
foreslått_url: "cloud247.no/blogg/hva-er-mta-sts-og-tls-rpt"
interne_lenker:
  - "https://dmarc.cloud247.no/ (DMARC-produktet, TLS-RPT- og MTA-STS-sjekk, med UTM)"
  - "https://domainguard.cloud247.no/ (DomainGuard, med UTM)"
  - "https://dmarc.cloud247.no/guider/dmarc-i-microsoft-365"
  - "cloud247.no/blogg/noen-sender-e-post-i-ditt-navn"
  - "cloud247.no/blogg/hva-koster-dmarc-overvaking"
---

# Hva er MTA-STS og TLS-RPT? En praktisk forklaring

SPF, DKIM og DMARC handler om hvem som får sende e-post i ditt navn. MTA-STS og TLS-RPT handler om noe annet: at e-post som sendes til deg, blir kryptert på veien og ikke kan fanges opp eller sendes til feil server.

Her er hva de to standardene gjør, hvordan du setter dem opp, og hvilke feil som er vanlige.

## Problemet: kryptering som kan skrus av

Når en e-postserver leverer e-post til domenet ditt, slår den opp MX-posten og kobler seg til serveren som står der. De fleste servere bruker STARTTLS for å kryptere forbindelsen. Problemet er at STARTTLS er valgfritt. Hvis noen i nettverket mellom serverne fjerner tilbudet om kryptering, faller avsenderen som regel tilbake til ukryptert levering uten å si fra. Avsenderen sjekker heller ikke nødvendigvis at sertifikatet hører til riktig server.

Det betyr at e-post til `post@eksempel.no` i verste fall kan leses eller sendes til en falsk server, uten at verken avsender eller mottaker merker noe.

## Hva MTA-STS gjør

MTA-STS (Mail Transfer Agent Strict Transport Security, RFC 8461) lar deg publisere en regel: «E-post til mitt domene skal bare leveres over TLS, med gyldig sertifikat, til disse MX-serverne.» Avsendere som støtter MTA-STS, henter regelen og følger den. Kan de ikke levere sikkert, leverer de ikke.

MTA-STS består av to deler.

### 1. Policyfilen

En tekstfil som ligger på HTTPS på en fast adresse:

```
https://mta-sts.eksempel.no/.well-known/mta-sts.txt
```

Innholdet ser slik ut for et domene som bruker Microsoft 365:

```
version: STSv1
mode: testing
mx: *.mail.protection.outlook.com
max_age: 86400
```

- `version` er alltid `STSv1`.
- `mode` er `testing`, `enforce` eller `none`.
- `mx` lister MX-serverne som er godkjent. Det kan være flere linjer, og jokertegn er lov for ett nivå.
- `max_age` sier hvor mange sekunder avsenderen skal huske policyen (maks 31 557 600, omtrent ett år).

Filen må leveres over HTTPS med gyldig sertifikat for `mta-sts.eksempel.no`.

### 2. TXT-posten `_mta-sts`

En DNS-post som forteller at policyen finnes, og hvilken versjon den har:

```
_mta-sts.eksempel.no  TXT  "v=STSv1; id=20261017T1200"
```

`id` er en fri tekst (bokstaver og tall) som må endres hver gang du endrer policyfilen. Det er slik avsenderne vet at de skal hente policyen på nytt. Mange bruker dato og klokkeslett. Glemmer du å endre `id`, kan avsendere fortsette å bruke den gamle policyen til `max_age` går ut.

## Testing før enforce

Begynn alltid med `mode: testing`. Da følger avsenderne ikke policyen strengt, men de rapporterer hvis levering ville ha feilet. Det er her TLS-RPT kommer inn.

Gå til `mode: enforce` først når rapportene viser at alt fungerer. Husk å endre `id` i TXT-posten samtidig. Når du er sikker på at oppsettet er stabilt, kan du øke `max_age`, for eksempel til en uke eller mer.

## Hva TLS-RPT gjør

TLS-RPT (SMTP TLS Reporting, RFC 8460) gir deg rapporter fra avsenderne om hvordan TLS-leveringen til domenet ditt gikk: hvor mange forbindelser som lyktes, og hvilke som feilet og hvorfor. Det settes opp med én TXT-post:

```
_smtp._tls.eksempel.no  TXT  "v=TLSRPTv1; rua=mailto:tlsrpt@eksempel.no"
```

Rapportene kommer som JSON-filer, vanligvis daglig. De viser feil som:

- sertifikatet passer ikke til vertsnavnet
- sertifikatet er utløpt
- policyfilen kunne ikke hentes
- MX-serveren står ikke i policyen

TLS-RPT er nyttig selv uten MTA-STS, men de to hører sammen. Uten rapportene setter du MTA-STS i `enforce` i blinde.

## Vanlige feil

1. **Policyfilen kan ikke hentes.** Feil sertifikat på `mta-sts.eksempel.no`, en videresending (redirect) eller en bot-beskyttelse som viser en sjekkside i stedet for filen. Avsenderservere er ikke nettlesere og kan ikke løse slike sjekker. Test at filen svarer med statuskode 200 og ren tekst.
2. **`id` endres ikke.** Du bytter MX eller går til `enforce`, men avsenderne bruker den gamle policyen.
3. **MX mangler i policyen.** Du legger til en ny MX-server, for eksempel ved bytte av e-postfilter, men glemmer policyfilen. I `enforce` blir e-post til den serveren ikke levert.
4. **Rett til enforce.** Uten en periode i `testing` og TLS-rapporter vet du ikke om noe vil feile.
5. **Ingen leser rapportene.** TLS-RPT-rapporter som havner i en postkasse ingen åpner, hjelper ikke.

## Hva med Microsoft 365?

Exchange Online tilbyr TLS på sine MX-servere med gyldige sertifikater for `*.mail.protection.outlook.com`, så det ligger godt til rette. Men selve policyfilen må du publisere selv, på et nettsted du styrer under `mta-sts.<ditt domene>`. TXT-postene for `_mta-sts` og TLS-RPT legges i DNS-en din som vanlig.

## Vanlige spørsmål

**Trenger jeg MTA-STS hvis jeg har DMARC?**
De løser ulike problemer. DMARC beskytter mot at noen sender e-post i ditt navn. MTA-STS beskytter e-post som sendes til deg, mot avlytting og omdirigering underveis.

**Hva skjer hvis policyfilen blir utilgjengelig?**
Avsendere som allerede har hentet policyen, bruker den de har lagret til `max_age` går ut. Nye avsendere finner ingen gyldig policy og leverer som før.

**Hvor ofte må jeg endre `id`?**
Hver gang innholdet i policyfilen endres, for eksempel når du bytter MX eller går fra `testing` til `enforce`.

**Kan jeg bruke TLS-RPT uten MTA-STS?**
Ja. Du får rapporter om TLS-feil uansett, og det er et fornuftig første steg før du innfører MTA-STS.

## Kort oppsummert

- MTA-STS gjør kryptert levering av e-post til domenet ditt obligatorisk for avsendere som støtter standarden.
- Den består av en policyfil på `mta-sts.<domene>/.well-known/mta-sts.txt` og en `_mta-sts`-TXT-post med en `id` som endres ved hver policyendring.
- Start i `testing`, les TLS-RPT-rapportene, og gå til `enforce` når de er rene.
- Sjekk resten av e-postoppsettet (SPF, DKIM og DMARC) med [DomainGuard](https://domainguard.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=mtasts-domainguard).

**Vil du vite om oppsettet faktisk virker?** Cloud247 DMARC gjør DMARC- og TLS-rapportene om til en oversikt og har innebygd TLS-RPT- og MTA-STS-sjekk, så du ser feilene før du går til enforce. [Prøv Cloud247 DMARC gratis i 14 dager](https://dmarc.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=mtasts-cta-bunn).
