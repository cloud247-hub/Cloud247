---
tittel: "Noen sender e-post fra domenet ditt? Slik stopper du det"
publisert: "2026-09-26"
metabeskrivelse: "Får kunder e-post som ser ut til å komme fra deg? Slik skjer e-postforfalskning, slik sjekker du SPF, DKIM og DMARC, og hvorfor p=none ikke stopper noe."
målsøk:
  - "noen sender e-post fra mitt domene"
  - "e-postforfalskning"
foreslått_url: "cloud247.no/blogg/noen-sender-e-post-i-ditt-navn"
interne_lenker:
  - "https://mailscore.cloud247.no/ (Mail Secure Score, med UTM)"
  - "https://domainguard.cloud247.no/ (DomainGuard, med UTM)"
  - "https://dmarc.cloud247.no/ (DMARC-produktet, med UTM)"
  - "https://dmarc.cloud247.no/guider/fra-p-none-til-p-reject"
  - "https://dmarc.cloud247.no/guider/dmarc-i-microsoft-365"
  - "cloud247.no/blogg/spf-feiler-10-oppslag"
  - "cloud247.no/blogg/hva-koster-dmarc-overvaking"
---

# Noen sender e-post fra domenet ditt? Slik stopper du det

En kunde ringer og spør om fakturaen dere sendte i går, den med nytt kontonummer. Dere har ikke sendt noen faktura. E-posten kom tilsynelatende fra `faktura@eksempel.no`, med logoen deres og riktig signatur.

Det er e-postforfalskning (spoofing), og det er overraskende enkelt å få til hvis domenet ikke er beskyttet. Her er hvordan det skjer, hvordan du sjekker ditt eget domene, og hva som faktisk stopper det.

## Hvordan e-postforfalskning skjer

E-post ble laget uten innebygd kontroll av hvem som er avsender. Avsenderen som vises i e-postprogrammet («From»), er bare et tekstfelt som den som sender, fyller ut selv. Hvem som helst med en e-postserver kan skrive `faktura@eksempel.no` der.

Det finnes tre varianter du bør kjenne til:

1. **Direkte forfalskning av domenet ditt.** Avsenderen er nøyaktig ditt domene, `eksempel.no`. Dette er det SPF, DKIM og DMARC er laget for å stoppe.
2. **Lignende domener.** Avsenderen bruker `eksempel-no.com` eller `eksernpel.no` (rn i stedet for m). DMARC på ditt domene hjelper ikke her, fordi det er et annet domene. Her må du være oppmerksom og lære opp brukerne.
3. **Kaprede kontoer.** Noen har fått tak i passordet til en ekte postkasse og sender fra den. E-posten passerer alle sjekker fordi den faktisk kommer fra dere. Her hjelper flerfaktorautentisering og innloggingsovervåking, ikke DNS-poster.

Resten av innlegget handler om den første varianten, fordi den kan du lukke helt.

## De tre sjekkene: SPF, DKIM og DMARC

**SPF** er en DNS-post som lister hvilke servere som har lov til å sende for domenet ditt. Svakheten er at SPF sjekker envelope-from (Return-Path), ikke avsenderen mottakeren ser. Les mer i innlegget om [SPF og grensen på 10 DNS-oppslag](https://cloud247.no/blogg/spf-feiler-10-oppslag).

**DKIM** er en digital signatur som legges på hver e-post. Mottakeren henter den offentlige nøkkelen fra DNS og sjekker at e-posten ikke er endret og er signert av domenet. I Microsoft 365 skrus DKIM på i Microsoft Defender-portalen, med to CNAME-poster (`selector1._domainkey` og `selector2._domainkey`).

**DMARC** binder det sammen. DMARC krever at SPF eller DKIM ikke bare passerer, men også samsvarer med domenet i From-feltet. Og DMARC forteller mottakeren hva som skal skje når sjekken feiler:

```
_dmarc.eksempel.no  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@eksempel.no"
```

## Slik sjekker du ditt eget domene

Begynn med en rask sjekk utenfra:

- [Mail Secure Score](https://mailscore.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spoofing-mailscore) gir en samlet vurdering av e-postsikkerheten på domenet.
- [DomainGuard](https://domainguard.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spoofing-domainguard) sjekker DNSSEC, MX, SPF, DKIM, DMARC og flere viktige domeneinnstillinger, og gir forslag når noe mangler.

Se særlig etter dette:

| Funn | Hva det betyr |
|---|---|
| Ingen DMARC-post | Mottakere har ingen instruks. Forfalskede e-poster vurderes bare av mottakerens eget filter. |
| `p=none` | Du får rapporter, men ingenting blir stoppet. |
| SPF slutter med `+all` eller `?all` | SPF godkjenner i praksis alle avsendere. |
| DKIM ikke aktivert | Bare SPF kan gi DMARC-pass, og SPF brytes ofte ved videresending. |

Har du fått en mistenkelig e-post, kan du også se i headerne. Se etter `Authentication-Results`. Der står det `spf=`, `dkim=` og `dmarc=` med resultatet `pass` eller `fail`.

## Hvorfor p=none ikke stopper noe

Mange har lagt inn DMARC og tror domenet er beskyttet. Men en DMARC-post med `p=none` betyr: «Send meg rapporter, men ikke gjør noe med e-post som feiler.» En forfalsket faktura fra `faktura@eksempel.no` blir levert akkurat som før, med mindre mottakerens eget spamfilter tilfeldigvis stopper den.

`p=none` er riktig som første steg, for rapportene viser hvem som sender e-post i ditt navn. Men det er bare starten. Det som faktisk beskytter, er:

- `p=quarantine`: e-post som feiler, legges i søppelpost.
- `p=reject`: e-post som feiler, avvises.

Grunnen til at mange blir stående på `p=none`, er frykten for å stoppe egen, legitim e-post. Nyhetsbrevverktøyet, fakturasystemet eller CRM-et kan sende uten riktig SPF eller DKIM. Går du rett til `p=reject`, kan de e-postene forsvinne.

## Veien fra p=none til p=reject

1. **Legg inn DMARC med `p=none` og en rapportadresse (`rua`).** Da begynner mottakere som Microsoft, Google og Yahoo å sende daglige rapporter.
2. **Les rapportene.** De er XML-filer som er tunge å lese manuelt. Se etter hvilke IP-adresser og tjenester som sender, og om de passerer SPF og DKIM med samsvar.
3. **Rett opp legitime avsendere.** Slå på DKIM for hver tjeneste som støtter det, og rydd i SPF.
4. **Gå til `p=quarantine`,** gjerne med `pct` for en gradvis overgang, og følg med på rapportene.
5. **Gå til `p=reject`** når rapportene viser at all legitim e-post passerer.

Hele prosessen med eksempler står i guiden [Fra p=none til p=reject](https://dmarc.cloud247.no/guider/fra-p-none-til-p-reject). Bruker dere Microsoft 365, se også [DMARC i Microsoft 365](https://dmarc.cloud247.no/guider/dmarc-i-microsoft-365).

## Vanlige spørsmål

**Kan noen sende e-post fra domenet mitt selv om jeg har SPF?**
Ja. SPF sjekker envelope-from, ikke avsenderen mottakeren ser. Uten DMARC med `p=quarantine` eller `p=reject` kan From-feltet fortsatt forfalskes.

**Hvorfor får jeg retur av e-post jeg aldri har sendt?**
Noen har trolig sendt forfalsket e-post med ditt domene som avsender, og mottakerservere sender returmeldinger tilbake til adressen. Det er et tegn på at domenet ditt brukes, og at du bør sjekke DMARC-policyen.

**Hjelper DMARC mot lignende domener som eksempel-no.com?**
Nei. DMARC beskytter bare ditt eget domene. Lignende domener må oppdages på andre måter, og brukerne bør lære å se etter dem.

**Hvor lang tid tar det å komme til p=reject?**
Det kommer an på hvor mange tjenester som sender e-post for dere. Rapportene viser når all legitim e-post passerer, og det er der du bør vente på.

## Kort oppsummert

- From-feltet i e-post kan forfalskes, med mindre domenet er beskyttet med DMARC.
- SPF og DKIM er byggesteinene. DMARC kobler dem til avsenderadressen og sier hva som skal skje.
- `p=none` gir rapporter, men stopper ingenting. Målet er `p=reject`.
- Sjekk domenet ditt med [Mail Secure Score](https://mailscore.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spoofing-mailscore-oppsummering) eller [DomainGuard](https://domainguard.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spoofing-domainguard-oppsummering).

**Klar for å komme deg fra p=none?** Cloud247 DMARC gjør DMARC- og TLS-rapportene om til en oversikt over hvem som sender i ditt navn, og gir deg en trygg vei fra p=none til reject. Varsler kommer i Teams, data lagres i EU, og oppsettet er én DNS-endring. [Prøv Cloud247 DMARC gratis i 14 dager](https://dmarc.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=spoofing-cta-bunn).
