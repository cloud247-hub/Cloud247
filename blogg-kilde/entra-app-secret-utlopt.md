---
tittel: "Entra app-secret utløpt? Slik fornyer du uten nedetid"
publisert: "2026-10-17"
metabeskrivelse: "Client secret utløpt i Microsoft Entra ID (AADSTS7000222)? Slik finner du utløpsdatoen, fornyer uten nedetid og holder oversikt over app-secrets."
målsøk:
  - "Entra app secret utløpt"
  - "client secret expired Azure AD"
  - "AADSTS7000222"
foreslått_url: "cloud247.no/blogg/entra-app-secret-utlopt"
interne_lenker:
  - "https://expiry.cloud247.no/ (ExpiryGuard, med UTM)"
  - "cloud247.no/blogg/apple-push-sertifikat-utlopt"
  - "cloud247.no (Cloud Toolbox-forsiden)"
---

# Entra app-secret utløpt? Slik fornyer du uten nedetid

Integrasjonen mot regnskapssystemet har sluttet å synkronisere. Skanneren sender ikke lenger e-post via Microsoft Graph. Et skript som har kjørt hver natt i to år, feiler plutselig med `AADSTS7000222`. Ingen har endret noe, og det er nettopp poenget: client secret-en på app-registreringen har gått ut på dato.

Her er hva som skjer, hvordan du finner utløpsdatoene, og hvordan du bytter secret uten at noe stopper.

## Hva en app-secret er

Når et program eller en tjeneste skal snakke med Microsoft 365 uten at en bruker logger inn, bruker det en *app-registrering* i Microsoft Entra ID. Appen må bevise hvem den er, og det gjør den med en legitimasjon:

- **Client secret** (app-passord): en tekststreng appen sender med når den ber om token.
- **Sertifikat**: appen signerer forespørselen med en privat nøkkel, og Entra kontrollerer den mot det offentlige sertifikatet du har lastet opp.
- **Federert legitimasjon**: appen får token fra en annen identitetsleverandør, for eksempel GitHub Actions, uten egen secret.

Microsoft anbefaler sertifikat eller federert legitimasjon i produksjon, og skriver at client secrets er mindre sikre. I praksis er client secrets likevel svært vanlige i SMB-miljøer, særlig i integrasjoner satt opp av leverandører.

## Hva skjer når secret-en utløper

En client secret har alltid en utløpsdato. Når datoen passeres, avviser Entra ID forespørsler med den. Feilen appen får, er typisk:

```
AADSTS7000222: InvalidClientSecretExpiredKeysProvided - The provided client secret keys are expired.
```

Konsekvensen avhenger av hva appen gjør:

- Synkronisering mot ERP, CRM eller lønnssystem stopper.
- Skannere og fagsystemer som sender e-post via Graph, slutter å sende.
- Backup av Microsoft 365 eller automatiseringsskript feiler, ofte uten at noen merker det før dataene trengs.

Det samme skjer når et sertifikat på app-registreringen utløper. Feilmeldingen blir en annen, men resultatet er det samme: appen får ikke token.

Får du i stedet `AADSTS7000215` (ugyldig client secret), er secret-en gyldig, men appen sender feil verdi. Det skjer ofte rett etter et bytte, hvis den gamle verdien fortsatt ligger igjen et sted.

## Maks levetid

I Entra-portalen kan en client secret ha en levetid på maks 24 måneder. Microsoft anbefaler under 12 måneder. Lager du secret via Microsoft Graph uten å angi sluttdato, blir standarden to år fra start.

Kortere levetid er sikrere, men gir flere fornyelser. Det er grunnen til at oversikten over utløpsdatoer betyr så mye.

## Slik finner du utløpsdatoen

### I Entra-portalen

1. Logg inn i Microsoft Entra admin center.
2. Gå til **App registrations** og velg appen.
3. Velg **Certificates & secrets**. Under fanene **Client secrets** og **Certificates** ser du hver legitimasjon med utløpsdato.

Det fungerer for én app. Har tenanten mange app-registreringer, eller du er MSP med mange tenanter, blir det fort tungvint.

### Med Microsoft Graph PowerShell

Dette lister alle client secrets og sertifikater i tenanten, sortert etter utløpsdato:

```powershell
Connect-MgGraph -Scopes "Application.Read.All"

Get-MgApplication -All -Property Id,AppId,DisplayName,PasswordCredentials,KeyCredentials |
  ForEach-Object {
    $app = $_
    foreach ($s in $app.PasswordCredentials) {
      [pscustomobject]@{ App = $app.DisplayName; Type = "Secret"; Navn = $s.DisplayName; Utløper = $s.EndDateTime }
    }
    foreach ($c in $app.KeyCredentials) {
      [pscustomobject]@{ App = $app.DisplayName; Type = "Sertifikat"; Navn = $c.DisplayName; Utløper = $c.EndDateTime }
    }
  } | Sort-Object Utløper | Format-Table -AutoSize
```

Merk at `Get-MgApplication` ikke henter legitimasjonen med mindre du ber om `PasswordCredentials` og `KeyCredentials` i `-Property`. Datoene er i UTC.

## Slik fornyer du uten nedetid

En app-registrering kan ha flere gyldige secrets samtidig. Det er det som gjør et sømløst bytte mulig:

1. **Lag en ny secret før den gamle utløper.** I portalen: **Certificates & secrets** → **Client secrets** → **New client secret**. Gi den en beskrivelse som sier når og til hva, for eksempel `regnskap-2026-10`.
2. **Kopier verdien med en gang.** Verdien vises bare én gang. Lagre den i et passordhvelv eller Azure Key Vault, ikke i en e-post.
3. **Oppdater appen eller tjenesten** med den nye verdien. Det kan være i et fagsystem, en konfigurasjonsfil, Key Vault eller hos leverandøren.
4. **Kontroller at appen virker** med den nye secret-en. Se i påloggingsloggen for tjenestekontoer (service principal sign-ins) i Entra at den logger inn uten feil.
5. **Slett den gamle secret-en** når du er sikker på at ingenting bruker den.

Med PowerShell kan steg 1 og 5 se slik ut. `-ApplicationId` er objekt-ID-en til appen, ikke Application (client) ID:

```powershell
Connect-MgGraph -Scopes "Application.ReadWrite.All"

$params = @{ passwordCredential = @{ displayName = "regnskap-2026-10"; endDateTime = (Get-Date).AddMonths(12) } }
$ny = Add-MgApplicationPassword -ApplicationId $appObjectId -BodyParameter $params
$ny.SecretText   # vises bare nå

# Når appen er oppdatert og testet:
Remove-MgApplicationPassword -ApplicationId $appObjectId -KeyId $gammelKeyId
```

Bruker du en Azure DevOps-tjenestetilkobling som har laget service principal automatisk, skal secret-en ifølge Microsoft fornyes fra Azure DevOps og ikke direkte i Entra.

## Har den allerede utløpt?

Da er fremgangsmåten den samme, bare uten buffer: lag en ny secret, oppdater appen og test. Integrasjonen er nede til appen har fått ny verdi. Den gamle secret-en kan ikke forlenges.

## Hvorfor dette skjer så ofte

- **Ingen eier appen.** Den ble satt opp av en leverandør eller en konsulent som ikke lenger er involvert.
- **Ingen varsler.** Utløpsdatoen står i portalen, men ingen ser på den.
- **Mange tenanter.** For en MSP med mange kunder blir det mange app-registreringer, hver med sin egen dato.

## Vanlige spørsmål

**Kan jeg lage en client secret som aldri utløper?**
Nei, ikke i Entra-portalen i dag. Maks er 24 måneder, og Microsoft anbefaler under 12.

**Slutter appen å virke i det sekundet secret-en utløper?**
Nye tokenforespørsler med den utløpte secret-en avvises. Et token som allerede er utstedt, kan virke til det selv utløper, men deretter stopper det.

**Kan jeg ha to secrets på samme app samtidig?**
Ja. Det er nettopp det som gjør at du kan bytte uten nedetid.

**Bør vi bytte til sertifikat?**
Microsoft anbefaler sertifikat eller federert legitimasjon i produksjon. Sertifikater har også en utløpsdato og må følges opp på samme måte.

## Kort oppsummert

- En utløpt client secret gir `AADSTS7000222`, og integrasjonen slutter å virke.
- Finn utløpsdatoene under **Certificates & secrets** eller med `Get-MgApplication` i Microsoft Graph PowerShell.
- Forny uten nedetid: legg til ny secret, oppdater appen, test, og slett den gamle.
- Maks levetid i portalen er 24 måneder, og Microsoft anbefaler under 12.

**Vil du vite om app-secrets før de utløper?** ExpiryGuard overvåker Microsoft Entra app-secrets via Microsoft Graph, sammen med Apple MDM Push-sertifikater, ADE-tokens og Apps & Books/VPP-tokens. Du får nedtelling, fornyelsesplan, arbeidskø og varsler i Teams og på e-post per kunde. Laget for både interne IT-avdelinger og MSP-er. [Prøv ExpiryGuard gratis i 14 dager](https://expiry.cloud247.no/?utm_source=blogg&utm_medium=blog&utm_campaign=uke43-blogg&utm_content=entra-cta-bunn).

<!--
Kilder (sjekket 17.10.2026):
- Microsoft Learn: Add and manage app credentials in Microsoft Entra ID – https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials
  (sertifikat anbefalt; client secrets mindre sikre; maks 24 måneder, anbefalt under 12; verdi vises bare én gang; sti Certificates & secrets; Azure DevOps-merknad)
- Microsoft Learn: Microsoft Entra authentication & authorization error codes – https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes
  (AADSTS7000222 InvalidClientSecretExpiredKeysProvided; AADSTS7000215 Invalid client secret is provided)
- Microsoft Graph: passwordCredential resource type – https://learn.microsoft.com/en-us/graph/api/resources/passwordcredential (endDateTime i UTC)
- Microsoft Graph: application: addPassword – https://learn.microsoft.com/en-us/graph/api/application-addpassword (Add-MgApplicationPassword, standard sluttdato start + 2 år, Application.ReadWrite.All, secretText bare ved opprettelse)
- Microsoft Graph: application: removePassword – https://learn.microsoft.com/en-us/graph/api/application-removepassword
- Microsoft Learn: PowerShell sample – Export app registrations with expiring secrets and certificates – https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/scripts/powershell-export-apps-with-expiring-secrets
-->
