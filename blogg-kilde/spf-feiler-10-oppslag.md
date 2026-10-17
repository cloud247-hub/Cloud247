---
tittel: "SPF permerror: for mange DNS-oppslag – slik retter du det"
publisert: "2026-09-19"
metabeskrivelse: "Får du SPF permerror? Slik fungerer grensen på 10 DNS-oppslag, de vanligste feilene i SPF-posten for Microsoft 365, og hvordan du retter dem."
målsøk:
  - "SPF permerror for mange DNS-oppslag"
  - "SPF-post Microsoft 365"
foreslått_url: "cloud247.no/blogg/spf-feiler-10-oppslag"
interne_lenker:
  - "https://spf.cloud247.no/ (SPF Record Checker, med UTM)"
  - "https://dmarc.cloud247.no/guider/dmarc-i-microsoft-365"
  - "https://dmarc.cloud247.no/guider/fra-p-none-til-p-reject"
  - "cloud247.no/blogg/noen-sender-e-post-i-ditt-navn"
  - "cloud247.no/blogg/hva-koster-dmarc-overvaking"
---

# SPF permerror: for mange DNS-oppslag – slik retter du det

Du har lagt inn SPF for Microsoft 365, så kom nyhetsbrevverktøyet, deretter CRM-systemet, fakturaløsningen og supportsystemet. Alle ba deg legge til «bare én include». Plutselig viser en sjekk `permerror`, og e-post som før gikk fint, havner i søppelpost eller avvises.

Årsaken er nesten alltid den samme: SPF-posten krever mer enn 10 DNS-oppslag. Her er hva det betyr, hvilke feil som er vanligst, og hvordan du rydder opp.

## Hva SPF gjør

SPF (Sender Policy Framework) er en TXT-post i DNS som sier hvilke servere som har lov til å sende e-post for domenet ditt. Når en mottakerserver får en e-post fra `post@eksempel.no`, slår den opp SPF-posten til eksempel.no og sjekker om IP-adressen som leverte e-posten, står på listen.

En enkel SPF-post for et domene som bare sender via Microsoft 365, ser slik ut:

```
v=spf1 include:spf.protection.outlook.com -all
```

- `v=spf1` sier at dette er en SPF-post.
- `include:spf.protection.outlook.com` henter inn Microsofts liste over sendeservere.
- `-all` sier at alle andre skal avvises.

## Grensen på 10 DNS-oppslag

SPF-standarden (RFC 7208) setter en grense: mottakeren skal ikke gjøre mer enn 10 DNS-oppslag for å evaluere SPF-posten. Blir grensen passert, er resultatet `permerror`, og SPF regnes som feilet.

Det som teller som oppslag, er mekanismene `include`, `a`, `mx`, `ptr`, `exists` og modifikatoren `redirect`. `ip4`, `ip6` og `all` teller ikke.

Det som overrasker mange, er at oppslagene i en include også teller. Ta dette eksempelet:

```
v=spf1 include:spf.protection.outlook.com include:_spf.nyhetsbrev.example include:mail.crm.example include:spf.faktura.example include:_spf.support.example mx a -all
```

Det ser ut som sju oppslag. Men hvis `_spf.nyhetsbrev.example` selv inneholder tre include-er, og CRM-leverandøren har to, er du allerede over grensen. Du ser det ikke i din egen post. Du må følge hele kjeden.

I tillegg har standarden en grense på to «tomme» oppslag (void lookups), altså oppslag som ikke gir svar. En include som peker på et domene som ikke lenger finnes, kan derfor også gi feil.

## De vanligste feilene

### 1. Flere SPF-poster på samme domene

Et domene skal ha én TXT-post som begynner med `v=spf1`. Har du to, for eksempel én fra den gamle e-postleverandøren og én for Microsoft 365, er resultatet `permerror` uansett hva postene inneholder.

Feil:

```
eksempel.no  TXT  "v=spf1 include:spf.protection.outlook.com -all"
eksempel.no  TXT  "v=spf1 include:_spf.gammel-leverandor.example ~all"
```

Riktig er å slå dem sammen til én post, eller fjerne den gamle hvis tjenesten ikke er i bruk.

### 2. Include for alle tjenester, også de som ikke trenger det

Mange tjenester sender med sitt eget domene i envelope-from (Return-Path), selv om avsenderen som vises, er ditt domene. Da sjekkes SPF mot deres domene, ikke ditt, og include-en din gjør ingenting annet enn å bruke opp oppslag. Sjekk dokumentasjonen til tjenesten eller headerne i en e-post de har sendt før du legger til en include.

### 3. Gamle tjenester som aldri ble fjernet

Byttet dere nyhetsbrevverktøy for to år siden? Ofte står den gamle include-en fortsatt. Gå gjennom listen og spør: sender denne tjenesten faktisk e-post for oss i dag?

### 4. `mx` og `a` uten grunn

`mx` og `a` gir mening hvis e-posten sendes fra de samme serverne som tar imot e-post eller er vert for nettsiden. Med Microsoft 365 er det sjelden tilfelle. MX peker til Exchange Online, som allerede dekkes av Microsofts include.

### 5. `~all` eller `-all`

`~all` (softfail) sier «trolig ikke godkjent», mens `-all` (hardfail) sier «ikke godkjent». Ingen av dem er feil i seg selv. Microsoft bruker `-all` i sine eksempler. Hvis du har DMARC med `p=reject` eller `p=quarantine`, er det DMARC-policyen som avgjør hva som skjer med e-post som feiler, og mange velger da `~all`. Det viktigste er at posten ikke slutter med `+all` eller `?all`. Da betyr SPF i praksis ingenting.

## Slik retter du SPF-posten

1. **Kartlegg hvem som sender.** List opp alle tjenester som sender e-post med domenet ditt: Microsoft 365, nyhetsbrev, CRM, faktura, support, skrivere og nettbutikk. DMARC-rapporter viser dette svart på hvitt, fordi de forteller hvilke IP-adresser som har sendt e-post i ditt navn.
2. **Tell oppslagene i hele kjeden.** Lim inn domenet i [SPF Record Checker](https://spf.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spf-verktoy-tell). Den følger include og redirect, teller DNS-oppslag og viser løkker og policyproblemer.
3. **Fjern det som ikke trengs.** Gamle tjenester, `mx`, `a` og `ptr` (som standarden fraråder) går først.
4. **Flytt tjenester til eget underdomene.** Nyhetsbrev kan ofte sendes fra for eksempel `nyhet.eksempel.no`, med sin egen SPF-post. Da teller ikke oppslagene mot hoveddomenet.
5. **Bruk `ip4`/`ip6` der det er stabilt.** Har du en egen server med fast IP, for eksempel en skriver som sender skannede dokumenter, er `ip4:` gratis i oppslagsregnskapet.
6. **Vær forsiktig med «flatting».** Å erstatte include-er med lange lister av IP-adresser kan få deg under grensen, men leverandørene endrer IP-adressene sine. Da må noen holde listen oppdatert.
7. **Test på nytt** etter endringen og vent til DNS har oppdatert seg.

## SPF alene er ikke nok

SPF sjekker envelope-from, ikke avsenderen mottakeren ser i e-postprogrammet. Derfor stopper ikke SPF alene forfalskede e-poster. Det er DMARC som kobler SPF og DKIM til avsenderadressen og forteller mottakeren hva som skal skje når sjekken feiler. Les mer i guiden [DMARC i Microsoft 365](https://dmarc.cloud247.no/guider/dmarc-i-microsoft-365) og i innlegget om [hva du gjør når noen sender e-post i ditt navn](https://cloud247.no/blogg/noen-sender-e-post-i-ditt-navn).

## Vanlige spørsmål

**Hvilken SPF-post trenger jeg for Microsoft 365?**
Sender du bare via Microsoft 365, holder det med `v=spf1 include:spf.protection.outlook.com -all`. Andre tjenester som sender med ditt domene i envelope-from, må legges til.

**Teller `ip4` og `ip6` mot grensen på 10?**
Nei. Bare `include`, `a`, `mx`, `ptr`, `exists` og `redirect` gir DNS-oppslag.

**Kan jeg ha to SPF-poster, én per tjeneste?**
Nei. To TXT-poster som begynner med `v=spf1` på samme navn gir `permerror`. Slå dem sammen til én.

**Påvirker SPF-feil DMARC?**
Ja. DMARC godtar e-posten hvis SPF eller DKIM passerer og samsvarer med avsenderdomenet. Feiler SPF, står DKIM alene. Feiler begge, slår DMARC-policyen inn.

## Kort oppsummert

- SPF-posten kan maks kreve 10 DNS-oppslag, inkludert alt som ligger i include-ene.
- Vanligste feil: flere SPF-poster, gamle tjenester, unødvendige include-er og `mx`/`a` uten grunn.
- Kartlegg hvem som sender, tell oppslagene med [SPF Record Checker](https://spf.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spf-verktoy-oppsummering), og rydd.
- SPF må kombineres med DKIM og DMARC for å stoppe forfalskning.

**Vil du se hvem som faktisk sender e-post i ditt navn?** Cloud247 DMARC gjør DMARC-rapportene om til en oversikt, slik at du ser hvilke tjenester som feiler SPF før du strammer inn. Det krever bare én DNS-endring. [Prøv Cloud247 DMARC gratis i 14 dager](https://dmarc.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spf-cta-bunn).
