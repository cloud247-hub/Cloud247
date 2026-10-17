---
tittel: "Slik setter du opp DANE i Microsoft 365 (Exchange Online)"
publisert: "2026-10-17"
canonical: "https://dmarc.cloud247.no/guider/dane-i-microsoft-365/"
metabeskrivelse: "Steg for steg: slå på innkommende SMTP DANE med DNSSEC i Exchange Online med PowerShell, sjekk at det virker og rull tilbake trygt."
maalsok:
  - "DANE Microsoft 365"
  - "sette opp DANE Exchange Online"
url: "https://dmarc.cloud247.no/guider/dane-i-microsoft-365"
status: "Utkast – ikke publisert"
interne_lenker:
  - "/guider/dmarc-i-microsoft-365"
  - "/guider/fra-p-none-til-p-reject"
  - "https://cloud247.no/blogg/hva-er-mta-sts-og-tls-rpt"
  - "https://mailscore.cloud247.no (Mail Secure Score)"
  - "https://domainguard.cloud247.no (DomainGuard)"
---

DMARC-overvåking › Guider › Slik setter du opp DANE i Microsoft 365

# Slik setter du opp DANE i Microsoft 365

Exchange Online støtter innkommende SMTP DANE med DNSSEC. Funksjonen er avslått som standard, og du slår den på per domene med PowerShell. Denne guiden viser fremgangsmåten slik Microsoft beskriver den, med `eksempel.no` som eksempeldomene. Bytt det ut med ditt eget.

## Hva er DANE, og hvorfor bry seg?

E-post mellom servere går over SMTP. TLS-kryptering brukes som regel «opportunistisk»: Den brukes hvis begge sider støtter det, ellers går e-posten i klartekst. I tillegg slår avsenderserveren opp MX-postene dine i DNS, og uten beskyttelse kan svarene forfalskes. Da kan e-post bli sendt til feil server eller nedgradert til ukryptert.

DANE (DNS-based Authentication of Named Entities) løser dette med en **TLSA-post** i DNS. Den forteller avsenderen hvilket sertifikat e-postserveren din skal ha. Avsenderen kobler til, setter opp TLS og sjekker at sertifikatet stemmer med TLSA-posten. Stemmer det ikke, blir ikke e-posten levert.

DANE bygger på **DNSSEC**, som signerer DNS-postene digitalt slik at mottakeren kan se at de er ekte og ikke endret underveis. Uten DNSSEC kan ikke TLSA-posten stoles på.

**Utgående DANE er allerede på.** For e-post du *sender* fra Exchange Online, gjør Microsoft DANE- og DNSSEC-sjekker automatisk når mottakerdomenet støtter det. Det er slått på for alle Exchange Online-kunder, og det finnes ikke noe valg for å slå det av. Det du må gjøre selv, er å slå på DANE for e-post du *mottar*.

## DANE og MTA-STS – velg ikke, bruk begge

MTA-STS og DANE har samme mål: å hindre nedgradering og avlytting av e-post mellom servere. Forskjellen er at DANE bruker DNSSEC for å bekrefte at DNS-svaret er ekte, mens MTA-STS stoler på sertifikatutstedere (CA). De kan brukes sammen. Microsofts fremgangsmåte tar høyde for at du har MTA-STS fra før, og PowerShell-sjekken kontrollerer at MTA-STS-policyen inneholder den nye MX-en. Les mer i [Hva er MTA-STS og TLS-RPT?](https://cloud247.no/blogg/hva-er-mta-sts-og-tls-rpt).

## Forutsetninger

Før du starter, bør dette være på plass:

1. **Domenet er verifisert og lagt til som akseptert domene (Accepted Domain)** og står som *Healthy* i Microsoft 365 Admin Center.
2. **MX-posten har prioritet 0 eller 10, og du har ingen reserve-MX.** Microsofts fremgangsmåte forutsetter dette. Har du en sekundær MX, må endringene planlegges ekstra nøye.
3. **DNSSEC er slått på for domenet ditt.** Microsoft skriver at du må aktivere DNSSEC på domenet for å få den fulle sikkerhetsgevinsten. Mange DNS-leverandører har DNSSEC som en innstilling.
4. **Tilgang til Exchange Online PowerShell** med rettigheter til å kjøre cmdletene nedenfor.

### DNSSEC for .no-domener

Norid har støttet DNSSEC for .no siden 2014, og anbefaler at alle registrarer tilbyr det. I praksis signerer DNS-leverandøren sonen din, og registraren legger inn DS-posten hos Norid. Registraren må være DNSSEC-aktivert hos Norid for å kunne gjøre det, og Norids registrarliste viser hvem som tilbyr DNSSEC. Sjekk dette hos din registrar og DNS-leverandør før du går videre.

### Begrensninger du bør kjenne til

Ifølge Microsoft gjelder dette i dag:

- **onmicrosoft.com-domener støttes ikke.** Det gjelder også tenantens første domene.
- **Domener opprettet via selvbetjent registrering («self service»/«viral») støttes ikke.**
- **Tredjeparts e-postgateway foran Exchange Online:** DANE sikrer bare trafikken fra gatewayen til Exchange Online hvis gatewayen selv støtter SMTP DANE med DNSSEC-validering.
- **Tredjepart på utgående vei** (e-post sendes via connector til en tjeneste og legges tilbake i Exchange Online): Tjenesten må slå opp den nye MX-en (`…mx.microsoft`) i DNS når den leverer tilbake. Ta kontakt med leverandøren før du starter.
- **Domener der Microsoft er DNS-vert (full NS-delegering):** Microsoft skriver at de har tenkt å støtte disse, men at de ikke vet når.

## Steg for steg: Slå på DNSSEC i Exchange Online

DNS-endringer kan ta tid å slå gjennom fordi svar mellomlagres flere steder. Sett av god tid, og gjør det gjerne utenom arbeidstid.

### 1. Senk TTL på dagens MX-post

Sett TTL på den eksisterende MX-posten så lavt som mulig, men ikke under 30 sekunder. Vent så til den gamle TTL-en har gått ut. Var den 3 600 sekunder, venter du én time.

**Bruker du MTA-STS?** Sett policyen til `mode: testing` og oppdater `id` i TXT-posten `_mta-sts` (Microsoft foreslår gjeldende tid i UTC). Vent til policyens `max_age` har gått ut før du fortsetter.

### 2. Koble til Exchange Online PowerShell

```powershell
Install-Module -Name ExchangeOnlineManagement   # bare første gang
Connect-ExchangeOnline -UserPrincipalName admin@eksempel.no
```

### 3. Kjør Enable-DnssecForVerifiedDomain

```powershell
Enable-DnssecForVerifiedDomain -DomainName eksempel.no
```

Kommandoen kan bruke noen minutter. Ved suksess får du `Result: Success` og en verdi i `DnssecMxValue`, for eksempel `eksempel-no.o-v1.mx.microsoft`. Det er navnet den nye MX-posten skal peke til. Bruk verdien du faktisk får.

### 4. Legg inn den nye MX-posten med prioritet 20

Hos DNS-leverandøren legger du inn en **ny** MX-post med `DnssecMxValue` som mål, prioritet **20** og så lav TTL som mulig (minst 30 sekunder). Den gamle MX-posten skal stå urørt foreløpig.

Med MTA-STS: Sjekk at modus fortsatt er `testing`. Bytt ut `mx`-linjen for den gamle MX-en med det nye vertsnavnet, og oppdater `id` i både policyen og TXT-posten.

**Har du gateway foran Exchange Online?** Da oppdaterer du i stedet målverten (smart host) i gatewayen til den nye verdien. Test med «DNSSEC Validation» i Microsoft Remote Connectivity Analyzer, og hopp til steg 8 hvis du også vil slå på DANE.

### 5. Test den nye MX-en

Kjør testen **Inbound SMTP Email** i [Microsoft Remote Connectivity Analyzer](https://testconnectivity.microsoft.com/tests/O365InboundSmtp/input). Utvid testtrinnene og sjekk at MX-en som slutter på `mx.microsoft`, ble testet uten feil. På grunn av mellomlagring kan det hende du må kjøre testen flere ganger.

### 6. Bytt prioritet

Sett den gamle MX-en (som peker til `mail.protection.outlook.com`) til prioritet **30**, og den nye (`…mx.microsoft`) til prioritet **0**.

### 7. Slett den gamle MX-posten

Slett MX-posten som slutter på `mail.protection.outlook.com`, `mail.eo.outlook.com` eller `mail.protection.outlook.de`. Sett så TTL på den nye MX-posten til 3 600 sekunder. Du kan kontrollere oppsettet med testen «DNSSEC Validation» (ikke «DANE Validation») i Remote Connectivity Analyzer.

## Steg for steg: Slå på DANE

### 8. Kjør Enable-SmtpDaneInbound

Når DNSSEC-delen er ferdig, slår du på DANE for det samme domenet:

```powershell
Enable-SmtpDaneInbound -DomainName eksempel.no
```

Svaret skal være `Result: Success`. Exchange Online legger da selv ut TLSA-postene. Du trenger ikke lage dem.

### 9. Vent på TLSA-postene og test

Microsoft oppgir at det kan ta 15–30 minutter før TLSA-postene er ute. Kjør deretter testen «DANE Validation [including DNSSEC]» i Remote Connectivity Analyzer.

Exchange Online publiserer **flere** TLSA-poster for å gjøre oppsettet mer robust, og det er normalt at noen av dem feiler i testen. Så lenge minst én TLSA-post blir godkjent, er DANE riktig satt opp.

### 10. Sett MTA-STS tilbake til enforce

Bruker du MTA-STS, setter du policyen tilbake til `mode: enforce` når du har bekreftet at e-posten kommer fram. Husk å oppdatere `id` i TXT-posten.

## Slik sjekker du at alt virker

Status for DNSSEC sjekker du med `Get-DnssecStatusForVerifiedDomain`. Kommandoen nedenfor viser de viktigste delresultatene i lesbar form:

```powershell
$r = Get-DnssecStatusForVerifiedDomain -DomainName eksempel.no
$r.DnssecFeatureStatus
$r.DnsValidation
"Forventet MX: $($r.ExpectedMxRecord.Record)"
$r.MxValidation
$r.MtaStsValidation
```

Du vil se `Enabled` for funksjonen og `Valid` for DNS-, MX- og MTA-STS-valideringen. Feil vises med koder. `EX003` betyr for eksempel at den nye MX-en ikke har prioritet 0, og `EX005` at den gamle MX-en fortsatt ligger der.

Status for DANE sjekker du med:

```powershell
Get-SmtpDaneInboundStatus -DomainName eksempel.no
```

### TLS-RPT: rapporter om hva som faktisk skjer

Remote Connectivity Analyzer viser bare at oppsettet er riktig der og da. Om leveringen virker i hverdagen, finner du ut med **TLS-RPT** (RFC 8460). Med en TXT-post på `_smtp._tls.eksempel.no` får du rapporter fra avsendere om vellykkede og mislykkede DANE- og MTA-STS-leveranser. Exchange Online sender rapportene som JSON.

```text
_smtp._tls.eksempel.no.  3600  IN  TXT  "v=TLSRPTv1; rua=mailto:tlsrpt@eksempel.no"
```

## Vanlige feil og tilbakerulling

**`DomainNotFound`:** Domenet finnes ikke blant de aksepterte domenene. Sjekk at det er verifisert i Microsoft 365 Admin Center og lagt til som akseptert domene i Exchange Admin Center.

**`DomainNotSupported`:** Du prøver med et onmicrosoft.com-domene.

**`PartitionNotFound`** (fra `Enable-SmtpDaneInbound`): DNSSEC er ikke slått på for domenet ennå. Gjør steg 1–7 først.

**`DnsSecOperationFailed`:** Kjør kommandoen på nytt senere.

Hvis e-post slutter å komme fram, finnes det tre måter å rulle tilbake på, avhengig av hva som feiler:

1. **DANE-valideringen feiler:** Slå av DANE.

   ```powershell
   Disable-SmtpDaneInbound -DomainName eksempel.no
   ```

2. **DNSSEC-valideringen feiler:** Slå av DNSSEC for domenet hos DNS-leverandøren, og be leverandøren om hjelp til å slå det trygt på igjen.

3. **Problemer med MX-verdien:** Legg inn en ny MX med prioritet 20 som peker til `<MX-token>.mail.protection.outlook.com`, for eksempel `eksempel-no.mail.protection.outlook.com`. Kontroller med Remote Connectivity Analyzer at den virker, og kjør så:

   ```powershell
   Disable-DnssecForVerifiedDomain -DomainName eksempel.no
   ```

   Slett deretter MX-en som slutter på `mx.microsoft`, og sett den gjenværende MX-en til prioritet 0.

## Vanlige spørsmål

**Må jeg gjøre noe for å bruke DANE på e-post jeg sender?**
Nei. Utgående DANE med DNSSEC er slått på for alle Exchange Online-kunder, og brukes når mottakerdomenet støtter det.

**Kan jeg bruke DANE og MTA-STS samtidig?**
Ja. Microsofts fremgangsmåte er laget for at de skal fungere sammen. Sett MTA-STS i `testing` mens du bytter MX, og tilbake til `enforce` etterpå.

**Må jeg lage TLSA-postene selv?**
Nei. Når du kjører `Enable-SmtpDaneInbound`, legger Exchange Online ut TLSA-postene for deg.

**Hvilke feilkoder får avsendere hvis DANE feiler?**
Exchange Online bruker blant annet `4/5.7.321` (mottaker støtter ikke STARTTLS), `4/5.7.322` (sertifikatet er utløpt), `4/5.7.323` (DANE-valideringen feilet) og `4/5.7.324` (ugyldige DNSSEC-poster). Microsoft opplyser at DNSSEC-feil i dag kan dukke opp som den generelle feilen `4/5.4.312 DNS query failed`.

## Kort oppsummert

- Utgående DANE er allerede på i Exchange Online. Innkommende må du slå på selv, per domene.
- Slå på DNSSEC hos registrar og DNS-leverandør. For .no må registraren støtte DNSSEC hos Norid.
- Kjør `Enable-DnssecForVerifiedDomain`, legg inn den nye `…mx.microsoft`-MX-en, bytt prioritet og slett den gamle.
- Kjør `Enable-SmtpDaneInbound`, vent 15–30 minutter og test med Remote Connectivity Analyzer.
- Sjekk status med `Get-DnssecStatusForVerifiedDomain` og `Get-SmtpDaneInboundStatus`. Rull tilbake med `Disable-SmtpDaneInbound` eller `Disable-DnssecForVerifiedDomain`.
- DANE og MTA-STS kan brukes sammen, og TLS-RPT forteller deg om sikker levering faktisk virker.

Har du ikke fått DMARC på plass ennå, start med [DMARC i Microsoft 365](/guider/dmarc-i-microsoft-365) og [Fra p=none til p=reject](/guider/fra-p-none-til-p-reject). Vil du ha en rask sjekk av e-postsikkerheten på domenet, kan du teste det gratis i [Mail Secure Score](https://mailscore.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-dmarc&utm_content=dane-mailscore) og [DomainGuard](https://domainguard.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-dmarc&utm_content=dane-domainguard).

## Se om sikker levering faktisk virker

Etter at DANE er slått på, er det TLS-RPT-rapportene som viser om avsenderne faktisk klarer å levere sikkert til deg. Rapportene kommer som JSON og er tunge å lese. Cloud247 DMARC sjekker TLS-RPT- og MTA-STS-oppsettet ditt, gjør DMARC- og TLS-rapportene om til én oversikt og varsler deg i Teams. Du kommer i gang med én DNS-endring.

[Prøv Cloud247 DMARC gratis i 14 dager](https://dmarc.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-dmarc&utm_content=dane-cta-bunn)

<!--
KILDER (sjekket 17.10.2026):
- Microsoft Learn: How SMTP DNS-based Authentication of Named Entities (DANE) works
  https://learn.microsoft.com/en-us/exchange/security-and-compliance/how-dane-secures-email
  (hentet via https://learn.microsoft.com/en-us/purview/how-smtp-dane-works)
- Enable-DnssecForVerifiedDomain: https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/enable-dnssecforverifieddomain?view=exchange-ps
- Get-DnssecStatusForVerifiedDomain: https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-dnssecstatusforverifieddomain?view=exchange-ps
- Enable-SmtpDaneInbound: https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/enable-smtpdaneinbound?view=exchange-ps
- Get-SmtpDaneInboundStatus: https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-smtpdaneinboundstatus?view=exchange-ps
- Disable-SmtpDaneInbound: https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/disable-smtpdaneinbound?view=exchange-ps
- GA-status (MC711018, GA 22.10.2024, av som standard): https://mc.merill.net/message/MC711018
  og https://techcommunity.microsoft.com/blog/exchange/announcing-general-availability-of-inbound-smtp-dane-with-dnssec-for-exchange-on/4281292
- Remote Connectivity Analyzer: https://testconnectivity.microsoft.com/tests/O365InboundSmtp/input
- Norid, DNSSEC for .no: https://teknisk.norid.no/en/dns-informasjon/dnssec-for-no/
- Norid DPS: https://teknisk.norid.no/uploads/2022/02/DNSSEC_Policy_and_Practice_Statement_for_no-1e2.pdf
MERK: Microsofts fremgangsmåte sier prioritet 0 for ny MX; eksemplet i Get-DnssecStatusForVerifiedDomain viser prioritet 10. Guiden følger fremgangsmåten (0).
-->
