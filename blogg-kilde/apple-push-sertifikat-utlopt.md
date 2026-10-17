---
tittel: "Apple MDM push-sertifikat utløpt i Intune? Gjør dette"
publisert: "2026-10-03"
metabeskrivelse: "Har Apple MDM push-sertifikatet (APNs) utløpt i Intune? Slik fornyer du det uten å re-enrolle enheter, og hvilke Apple-tokens som også utløper hvert år."
målsøk:
  - "Apple MDM push-sertifikat utløpt Intune"
  - "APNs-sertifikat fornye Intune"
foreslått_url: "cloud247.no/blogg/apple-push-sertifikat-utlopt"
interne_lenker:
  - "https://expiry.cloud247.no/ (ExpiryGuard, med UTM)"
  - "cloud247.no (Cloud Toolbox-forsiden)"
  - "Kilde: Microsoft Learn – Get an Apple MDM Push certificate for Intune"
---

# Apple MDM push-sertifikat utløpt i Intune? Gjør dette

Mandag morgen: nye iPhoner kan ikke registreres i Intune, apper rulles ikke ut, og eksisterende iPader ser ut til å ha sluttet å hente nye innstillinger. I Intune står Apple MDM Push-sertifikatet som utløpt.

Det er en av de vanligste og mest unødvendige driftsstansene i et Microsoft 365-miljø med Apple-enheter. Sertifikatet utløper én gang i året, varselet går ofte til en postkasse ingen følger med på, og den som satte det opp, har kanskje sluttet.

Her er hva som skjer, hvordan du fikser det, og hvilke andre Apple-tokens du bør holde øye med.

## Hva Apple MDM Push-sertifikatet gjør

For at Intune skal kunne styre iPhone, iPad og Mac, må det kunne gi enhetene beskjed om å sjekke inn. Det skjer via Apple Push Notification service (APNs). Apple MDM Push-sertifikatet er det som gir Intune lov til å bruke APNs for organisasjonen din.

Ifølge Microsoft kreves sertifikatet for å administrere iOS/iPadOS- og macOS-enheter i Intune, både ved registrering via Company Portal og via Apple Business Manager, Apple School Manager og Apple Configurator.

Sertifikatet er gyldig i 365 dager og må fornyes hvert år.

## Hva skjer når sertifikatet utløper

Når APNs-sertifikatet er utløpt:

- **Nye Apple-enheter kan ikke registreres.** Registreringen feiler, ofte med feilmeldinger som `APNSCertificateNotValid` eller `NoEnrollmentPolicy`.
- **Eksisterende enheter kan ikke administreres som normalt.** Intune kan ikke varsle enhetene, så nye innstillinger, apper og kommandoer som fjernsletting når ikke frem.

Enhetene fortsetter å virke for brukeren, men de er i praksis ute av kontroll for IT.

## Fornyelse eller nytt sertifikat: forskjellen er avgjørende

Her ligger den største fellen. Microsoft skiller tydelig mellom å **fornye** sertifikatet og å **erstatte** det:

- **Fornyelse** gjøres med den samme Apple-ID-en som opprettet sertifikatet, og du velger det eksisterende sertifikatet i Apple Push Certificates Portal. Enhetene merker ingenting.
- **Nytt sertifikat** (med en annen Apple-ID, eller ved å velge «Create a Certificate» i stedet for «Renew») gir et sertifikat med ny identitet. Da må alle iOS/iPadOS-enheter registreres på nytt i Intune.

Etter at sertifikatet har utløpt, har du ifølge Microsoft 30 dagers frist til å fornye det. Går fristen ut, kan du ikke lenger fornye det samme sertifikatet, og du må re-enrolle enhetene.

For et firma med 40 iPader på lager og ute hos ansatte, er forskjellen en halvtime med fornyelse eller dager med manuelt arbeid.

## Slik fornyer du APNs-sertifikatet

1. Logg inn i Microsoft Intune admin center.
2. Gå til **Devices** → **Device onboarding** → **Enrollment** og velg fanen **Apple**.
3. Velg **Apple MDM Push Certificate**. Her ser du utløpsdatoen og hvilken Apple-ID som ble brukt.
4. Last ned CSR-filen med **Download your CSR**.
5. Velg **Create your MDM push Certificate** for å åpne Apple Push Certificates Portal, og logg inn med **den samme Apple-ID-en**.
6. Finn sertifikatet og velg **Renew**. Ikke velg «Create a Certificate».
7. Last opp CSR-filen, last ned det nye sertifikatet (.pem) og last det opp i Intune.

Fornyelsen er ferdig når sertifikatet vises som aktivt både i Intune og i Apples portal.

**Finner du ikke Apple-ID-en?** Den står i Intune under Apple MDM Push Certificate. Microsoft anbefaler å bruke en Apple-ID knyttet til en felles firmaadresse, for eksempel en distribusjonsliste, ikke en personlig konto. Har eieren sluttet og passordet er borte, må tilgangen til den Apple-ID-en gjenopprettes før du kan fornye.

## To andre Apple-tokens som også utløper hvert år

APNs-sertifikatet er ikke det eneste. Bruker dere Apple Business Manager, har dere sannsynligvis også disse:

### ADE-token (Automated Device Enrollment)

Enrollment program-tokenet kobler Apple Business Manager til Intune, slik at nye enheter registreres automatisk når de slås på første gang. Det må fornyes hvert år, og også hvis passordet til Apple-ID-en som satte det opp endres, eller personen slutter.

Utløper ADE-tokenet, stopper automatisk registrering av nye enheter. Ifølge Microsoft påvirker en fornyelse ikke enheter som allerede er registrert. Fornyelsen gjøres ved å laste ned tokenet på nytt i Apple Business Manager og laste det opp under **Enrollment program tokens** i Intune. Merk at nedlasting av et nytt token i Apple Business Manager gjør det gamle ugyldig, så fullfør opplastingen med en gang.

### Apps & Books-token (tidligere VPP)

Location-tokenet, som tidligere het VPP-token, brukes til å tildele app-lisenser kjøpt via Apple Business Manager. Hvert token er gyldig i ett år. Utløper det, vises det som ugyldig i Intune, og lisensbaserte apper kan ikke tildeles eller oppdateres som normalt. Fornyelse: last ned tokenet på nytt fra Apple Business Manager under **Apps and Books** og last det opp på det eksisterende tokenet under **Tenant administration** → **Connectors and tokens** → **Apple VPP tokens**.

## Hvorfor dette går galt så ofte

Tre ting går igjen:

1. **Varselet går til feil person.** Apple sender påminnelser til Apple-ID-en som opprettet sertifikatet. Var det en personlig adresse til en som har sluttet, leser ingen dem.
2. **Datoene ligger spredt.** APNs-sertifikatet, ADE-tokenet og Apps & Books-tokenet utløper på forskjellige datoer, og ofte kommer Entra app-secrets i tillegg.
3. **MSP-er har mange kunder.** For en MSP med 20 kundetenanter blir det fort mange datoer å holde styr på, hver med sin egen Apple-ID.

## Vanlige spørsmål

**Kan jeg fornye APNs-sertifikatet etter at det har utløpt?**
Ja, innen 30 dager etter utløp, ifølge Microsoft. Etter det må du lage et nytt sertifikat, og enhetene må registreres på nytt.

**Må enhetene registreres på nytt etter fornyelse?**
Nei, ikke hvis du fornyer det eksisterende sertifikatet med samme Apple-ID. Lager du et nytt sertifikat, må alle iOS/iPadOS-enheter registreres på nytt.

**Hvor ser jeg utløpsdatoen?**
I Intune admin center under Devices → Enrollment → Apple → Apple MDM Push Certificate. ADE-tokens står under Enrollment program tokens, og Apps & Books-tokens under Tenant administration → Connectors and tokens.

**Hva hvis jeg ikke vet hvilken Apple-ID som ble brukt?**
Den står i Intune sammen med sertifikatet. Du trenger tilgang til den kontoen for å fornye.

## Kort oppsummert

- Apple MDM Push-sertifikatet må fornyes hvert år. Utløper det, kan ikke Intune administrere Apple-enhetene som normalt.
- Forny alltid med samme Apple-ID og det eksisterende sertifikatet. Nytt sertifikat betyr re-enrollment av alle iOS/iPadOS-enheter.
- Du har 30 dager etter utløp til å fornye.
- ADE-tokenet og Apps & Books-tokenet utløper også årlig og bør følges opp på samme måte.

**Vil du slippe å holde styr på datoene selv?** ExpiryGuard overvåker Apple MDM Push-sertifikater, ADE-tokens, Apps & Books/VPP-tokens og Microsoft Entra app-secrets via Microsoft Graph. Du får nedtelling, fornyelsesplan, arbeidskø og varsler i Teams og på e-post per kunde. Laget for både interne IT-avdelinger og MSP-er. [Prøv ExpiryGuard gratis i 14 dager](https://expiry.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=apns-cta-bunn).
