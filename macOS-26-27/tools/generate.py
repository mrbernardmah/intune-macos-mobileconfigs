#!/usr/bin/env python3
"""
Generates the .mobileconfig files in this folder and the README profile table.

Usage:  python3 tools/generate.py        (run from macOS-26-27/)

Profiles are unsigned (Intune requires unsigned .mobileconfig for custom profiles).
UUIDs are deterministic (uuid5) so re-running produces identical files.
"""
import plistlib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NS = uuid.UUID("6f1f3a62-9c0e-4d57-8a41-0b7d2f6e1c10")
ORG = "Intune macOS Profiles (community)"
ID_PREFIX = "io.github.mrbernardmah.intune"

MS_TEAM = "UBF8T346G9"      # Microsoft Corporation
ZOOM_TEAM = "BJ4HAAB9B3"    # Zoom Video Communications

SPECS = []  # collected for README


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(parts))).upper()


def payload(slug, n, ptype, name, **content):
    d = {
        "PayloadType": ptype,
        "PayloadVersion": 1,
        "PayloadIdentifier": f"{ID_PREFIX}.{slug}.{n}",
        "PayloadUUID": uid(slug, str(n)),
        "PayloadDisplayName": name,
    }
    d.update(content)
    return d


def profile(folder, slug, title, desc, payloads, scope="System",
            os26="Yes", os27="Yes", note=""):
    """payloads: list of (ptype, display_name, content_dict)"""
    content = [payload(slug, i + 1, t, n, **c) for i, (t, n, c) in enumerate(payloads)]
    prof = {
        "PayloadType": "Configuration",
        "PayloadVersion": 1,
        "PayloadScope": scope,
        "PayloadIdentifier": f"{ID_PREFIX}.{slug}",
        "PayloadUUID": uid(slug),
        "PayloadDisplayName": title,
        "PayloadDescription": desc,
        "PayloadOrganization": ORG,
        "PayloadRemovalDisallowed": False,
        "PayloadContent": content,
    }
    out = ROOT / folder
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{slug}.mobileconfig"
    with open(path, "wb") as f:
        plistlib.dump(prof, f, sort_keys=False)
    SPECS.append(dict(folder=folder, file=path.name, title=title, scope=scope,
                      types=", ".join(sorted({p[0] for p in payloads})),
                      os26=os26, os27=os27, note=note))


def code_req(identifier, team):
    """Standard Developer ID requirement: bundle ID + Apple anchor + Developer ID CA +
    Developer ID Application leaf + Team ID. Same form as `codesign -dr -` prints for
    Developer ID apps. Verify per app with: codesign -dr - /Applications/<App>.app"""
    return (f'identifier "{identifier}" and anchor apple generic and '
            f'certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and '
            f'certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and '
            f'certificate leaf[subject.OU] = {team}')


# ===========================================================================
# 01 - Security
# ===========================================================================
F = "01-security"

profile(F, "passcode-policy", "Passcode Policy",
        "Local account password complexity. Prefer Intune's native Settings catalog if you also use Platform SSO password sync.",
        [("com.apple.mobiledevice.passwordpolicy", "Passcode", dict(
            forcePIN=True, allowSimple=False, requireAlphanumeric=True, minLength=12,
            minComplexChars=1, maxFailedAttempts=10, pinHistory=5,
            maxPINAgeInDays=0, maxGracePeriod=0))],
        note="Set maxPINAgeInDays > 0 only if you want forced rotation.")

profile(F, "filevault-enable-no-escrow", "FileVault - Enable (no escrow)",
        "Enables FileVault at next login. WARNING: this custom profile does NOT escrow the recovery key to Intune. Use Intune's native Endpoint security > Disk encryption > macOS FileVault policy in production.",
        [("com.apple.MCX.FileVault2", "FileVault", dict(
            Enable="On", Defer=True, UserEntersMissingInfo=False,
            ShowRecoveryKey=False, DeferForceAtUserLoginMaxBypassAttempts=0)),
         ("com.apple.MCX", "Prevent FileVault disable", dict(dontAllowFDEDisable=True))],
        note="Lab/testing only. Use native Intune FileVault policy for key escrow.")

profile(F, "firewall", "Firewall",
        "Enables the application firewall with stealth mode and logging.",
        [("com.apple.security.firewall", "Firewall", dict(
            EnableFirewall=True, BlockAllIncoming=False, EnableStealthMode=True,
            AllowSigned=True, AllowSignedApp=True, LoggingEnabled=True,
            LoggingOption="brief"))])

profile(F, "gatekeeper", "Gatekeeper",
        "Enforces Gatekeeper (App Store and identified developers) and prevents users overriding it.",
        [("com.apple.systempolicy.control", "Gatekeeper", dict(
            EnableAssessment=True, AllowIdentifiedDevelopers=True)),
         ("com.apple.systempolicy.managed", "Gatekeeper override", dict(
             DisableOverride=True))])

profile(F, "screensaver-lock", "Screen Saver and Lock",
        "Starts the screen saver after 10 minutes and requires a password 5 seconds later. User-channel profile.",
        [("com.apple.screensaver", "Screen saver", dict(
            askForPassword=True, askForPasswordDelay=5, idleTime=600,
            loginWindowIdleTime=600))],
        scope="User", note="Deploy to the user channel in Intune.")

profile(F, "local-accounts-no-guest", "Local Accounts - Disable Guest",
        "Disables the guest account and guest access to shared folders.",
        [("com.apple.MCX", "Guest account", dict(
            DisableGuestAccount=True, EnableGuestAccount=False))])

profile(F, "smartcard", "Smart Card Policy",
        "Allows smart card use and pairing, with certificate trust checking.",
        [("com.apple.security.smartcard", "Smart card", dict(
            allowSmartCard=True, UserPairing=True, CheckCertificateTrust=1,
            oneCardPerUser=False, tokenRemovalAction=0))])

# ===========================================================================
# 02 - Restrictions
# ===========================================================================
F = "02-restrictions"

profile(F, "restrictions-icloud", "Restrictions - iCloud",
        "Blocks iCloud sync of documents, desktop, keychain and other data.",
        [("com.apple.applicationaccess", "iCloud restrictions", dict(
            allowCloudDocumentSync=False, allowCloudDesktopAndDocuments=False,
            allowCloudKeychainSync=False, allowCloudMail=False,
            allowCloudAddressBook=False, allowCloudCalendar=False,
            allowCloudReminders=False, allowCloudBookmarks=False,
            allowCloudNotes=False, allowCloudPhotoLibrary=False))])

profile(F, "restrictions-hardening", "Restrictions - Hardening",
        "Disables AirDrop, manual profile installation and erase-all-content-and-settings.",
        [("com.apple.applicationaccess", "Hardening", dict(
            allowAirDrop=False, allowUIConfigurationProfileInstallation=False,
            allowEraseContentAndSettings=False))])

profile(F, "restrictions-diagnostics-ads", "Restrictions - Diagnostics and Ads",
        "Stops diagnostic submission to Apple and limits ad tracking.",
        [("com.apple.applicationaccess", "Diagnostics and ads", dict(
            allowDiagnosticSubmission=False, allowDiagnosticSubmissionModification=False,
            forceLimitAdTracking=True))])

profile(F, "appstore-restrictions", "App Store Restrictions",
        "Requires an administrator to install App Store apps and limits the store to software updates only if desired.",
        [("com.apple.appstore", "App Store", dict(
            **{"restrict-store-require-admin-to-install": True,
               "restrict-store-softwareupdate-only": False}))])

profile(F, "web-content-filter-builtin", "Web Content Filter (built-in)",
        "Apple's built-in web content filter for Safari with an example deny list.",
        [("com.apple.webcontent-filter", "Web content filter", dict(
            FilterType="BuiltIn", AutoFilterEnabled=True, FilterBrowsers=True,
            FilterSockets=False, PermittedURLs=[],
            DenyListURLs=["https://example-blocked.test"]))],
        note="Edit DenyListURLs. Safari only; use a vendor content filter for other browsers.")

# ===========================================================================
# 03 - Network
# ===========================================================================
F = "03-network"

profile(F, "wifi-wpa2-personal", "Wi-Fi - WPA2 Personal (template)",
        "Template. Replace SSID and password before deploying.",
        [("com.apple.wifi.managed", "Wi-Fi", dict(
            SSID_STR="REPLACE_SSID", HIDDEN_NETWORK=False, AutoJoin=True,
            CaptiveBypass=False, EncryptionType="WPA2", Password="REPLACE_PASSWORD",
            ProxyType="None"))],
        note="Template - edit SSID/password.")

profile(F, "wifi-eap-tls", "Wi-Fi - EAP-TLS with SCEP (template)",
        "Template. 802.1X EAP-TLS Wi-Fi with an in-profile SCEP identity. Replace SCEP URL, challenge, SSID and RADIUS names. In Intune, prefer native SCEP/PKCS + Wi-Fi profiles.",
        [("com.apple.security.scep", "SCEP identity", dict(
            URL="https://scep.example.com/certsrv/mscep/mscep.dll",
            Name="Wi-Fi identity", Subject=[[["CN", "%ComputerName%"]]],
            Challenge="REPLACE_CHALLENGE", Keysize=2048, KeyType="RSA",
            KeyUsage=5, Retries=3, RetryDelay=10)),
         ("com.apple.wifi.managed", "Wi-Fi 802.1X", dict(
             SSID_STR="REPLACE_SSID", HIDDEN_NETWORK=False, AutoJoin=True,
             EncryptionType="WPA2", ProxyType="None",
             PayloadCertificateUUID=uid("wifi-eap-tls", "1"),
             EAPClientConfiguration=dict(
                 AcceptEAPTypes=[13],
                 TLSTrustedServerNames=["radius.example.com"],
                 TLSMinimumVersion="1.2", TLSMaximumVersion="1.3")))],
        note="Template - SCEP and RADIUS values required.")

profile(F, "ethernet-8021x", "Ethernet - 802.1X EAP-TLS (template)",
        "Template. Wired 802.1X with an in-profile SCEP identity.",
        [("com.apple.security.scep", "SCEP identity", dict(
            URL="https://scep.example.com/certsrv/mscep/mscep.dll",
            Name="Ethernet identity", Subject=[[["CN", "%ComputerName%"]]],
            Challenge="REPLACE_CHALLENGE", Keysize=2048, KeyType="RSA",
            KeyUsage=5, Retries=3, RetryDelay=10)),
         ("com.apple.firstethernet.managed", "Ethernet 802.1X", dict(
             Interface="FirstActiveEthernet", AutoJoin=True,
             AuthenticationMethod="", SetupModes=["System"],
             PayloadCertificateUUID=uid("ethernet-8021x", "1"),
             EAPClientConfiguration=dict(
                 AcceptEAPTypes=[13],
                 TLSTrustedServerNames=["radius.example.com"],
                 TLSMinimumVersion="1.2", TLSMaximumVersion="1.3")))],
        note="Template - verify against your NAC. Native Intune wired profile recommended.")

profile(F, "vpn-ikev2", "VPN - IKEv2 (template)",
        "Template. IKEv2 with certificate auth. Algorithms meet macOS 26 minimums (no DES/3DES/SHA1, DH group 14+). Declarative VPN configurations arrive in macOS 27 but this payload still works.",
        [("com.apple.vpn.managed", "VPN", dict(
            UserDefinedName="Corporate VPN", VPNType="IKEv2",
            IKEv2=dict(
                RemoteAddress="vpn.example.com", LocalIdentifier="REPLACE_LOCAL_ID",
                RemoteIdentifier="vpn.example.com", AuthenticationMethod="Certificate",
                ExtendedAuthEnabled=0, DeadPeerDetectionRate="Medium",
                EnablePFS=1, DisableMOBIKE=0, DisableRedirect=0,
                IKESecurityAssociationParameters=dict(
                    EncryptionAlgorithm="AES-256-GCM", IntegrityAlgorithm="SHA2-256",
                    DiffieHellmanGroup=20, LifeTimeInMinutes=1440),
                ChildSecurityAssociationParameters=dict(
                    EncryptionAlgorithm="AES-256-GCM", IntegrityAlgorithm="SHA2-256",
                    DiffieHellmanGroup=20, LifeTimeInMinutes=1440))))],
        note="Template - edit server/identities; add a cert payload.")

profile(F, "dns-over-https", "DNS over HTTPS (template)",
        "Template. Encrypted DNS settings. Replace the server URL.",
        [("com.apple.dnsSettings.managed", "DNS settings", dict(
            DNSSettings=dict(DNSProtocol="HTTPS",
                             ServerURL="https://dns.example.com/dns-query",
                             ServerAddresses=["192.0.2.53", "2001:db8::53"]),
            OnDemandRules=[dict(Action="Connect")]))],
        note="Template - macOS 27 adds declarative DNS; this payload remains supported.")

# ===========================================================================
# 04 - Identity and certificates
# ===========================================================================
F = "04-identity"

_entra_urls = [
    "https://login.microsoftonline.com", "https://login.microsoft.com",
    "https://sts.windows.net", "https://login.partner.microsoftonline.cn",
    "https://login.chinacloudapi.cn", "https://login.microsoftonline.us",
    "https://login-us.microsoftonline.com"]

profile(F, "entra-enterprise-sso-redirect", "Microsoft Entra - Enterprise SSO Plug-in",
        "Redirect SSO app extension using the Company Portal extension (Microsoft Enterprise SSO plug-in). Requires Company Portal installed.",
        [("com.apple.extensiblesso", "Enterprise SSO", dict(
            ExtensionIdentifier="com.microsoft.CompanyPortalMac.ssoextension",
            TeamIdentifier=MS_TEAM, Type="Redirect", URLs=_entra_urls,
            ScreenLockedBehavior="DoNotHandle",
            ExtensionData={"AppPrefixAllowList": "com.microsoft.,com.apple.",
                           "browser_sso_interaction_enabled": 1,
                           "disable_explicit_app_prompt": 1}))],
        note="Company Portal must be installed first.")

profile(F, "entra-platform-sso", "Microsoft Entra - Platform SSO (Secure Enclave)",
        "Platform SSO with Secure Enclave key. Uses Intune's {{DEVICEREGISTRATION}} token. macOS 27 extends Platform SSO to FileVault unlock and lock screen; Intune's Settings catalog Platform SSO policy is preferred for new keys.",
        [("com.apple.extensiblesso", "Platform SSO", dict(
            ExtensionIdentifier="com.microsoft.CompanyPortalMac.ssoextension",
            TeamIdentifier=MS_TEAM, Type="Redirect", URLs=_entra_urls,
            ScreenLockedBehavior="DoNotHandle",
            ExtensionData={"device_registration": "{{DEVICEREGISTRATION}}",
                           "browser_sso_interaction_enabled": 1,
                           "disable_explicit_app_prompt": 1},
            PlatformSSO=dict(
                AuthenticationMethod="UserSecureEnclaveKey", UseSharedDeviceKeys=True,
                AccountDisplayName="Microsoft Entra ID", EnableAuthorization=True,
                EnableCreateUserAtLogin=True, NewUserAuthorizationMode="Standard",
                UserAuthorizationMode="Standard")))],
        note="Prefer Intune Settings catalog for new Platform SSO keys.")

profile(F, "scep-certificate", "SCEP Certificate (template)",
        "Template. Standalone SCEP client identity. In Intune use native SCEP profiles with the Certificate connector where possible.",
        [("com.apple.security.scep", "SCEP", dict(
            URL="https://scep.example.com/certsrv/mscep/mscep.dll",
            Name="Device identity", Subject=[[["CN", "%ComputerName%"]]],
            Challenge="REPLACE_CHALLENGE", Keysize=2048, KeyType="RSA",
            KeyUsage=5, Retries=3, RetryDelay=10))],
        note="Template. See tools/make-root-cert-profile.py for trusted root profiles.")

profile(F, "domains-autofill", "Managed Domains (template)",
        "Template. Marks domains for Safari password AutoFill and managed web/email domains.",
        [("com.apple.domains", "Domains", dict(
            SafariPasswordAutoFillDomains=["example.com"],
            WebDomains=["example.com"], EmailDomains=["example.com"]))],
        note="Template - edit domains.")

# ===========================================================================
# 05 - System, apps and management
# ===========================================================================
F = "05-system-apps"

profile(F, "managed-login-items-microsoft", "Managed Login Items - Microsoft",
        "Pre-approves Microsoft background items (Defender, Office, OneDrive, Teams, AutoUpdate) so users are not prompted.",
        [("com.apple.servicemanagement", "Managed login items", dict(
            Rules=[dict(RuleType="TeamIdentifier", RuleValue=MS_TEAM,
                        Comment="Microsoft Corporation")]))])

profile(F, "managed-login-items-template", "Managed Login Items (template)",
        "Template. Pre-approve background items by Team ID, bundle ID prefix or label.",
        [("com.apple.servicemanagement", "Managed login items", dict(
            Rules=[dict(RuleType="TeamIdentifier", RuleValue="REPLACE_TEAMID",
                        Comment="Vendor"),
                   dict(RuleType="BundleIdentifierPrefix", RuleValue="com.example.",
                        Comment="Example prefix")]))],
        note="Template - edit rules.")

profile(F, "system-extensions-template", "System Extensions (template)",
        "Template. Allow system extensions by Team ID and bundle identifier without user approval.",
        [("com.apple.system-extension-policy", "System extensions", dict(
            AllowUserOverrides=False,
            AllowedSystemExtensions={"REPLACE_TEAMID": ["com.example.app.sysext"]},
            AllowedSystemExtensionTypes={"REPLACE_TEAMID": [
                "EndpointSecurityExtension", "NetworkExtension"]}))],
        note="Template - edit Team ID/bundle IDs.")

profile(F, "setup-assistant-skip", "Setup Assistant - Skip Panes",
        "Skips optional Setup Assistant panes for new users. For ADE enrollments also set skip keys in the Intune enrollment profile; some panes (e.g. Age Range) cannot be skipped outside ADE on macOS 26.",
        [("com.apple.SetupAssistant.managed", "Setup Assistant", dict(
            SkipCloudSetup=True, SkipSiriSetup=True, SkipPrivacySetup=True,
            SkipiCloudStorageSetup=True, SkipTouchIDSetup=True,
            SkipScreenTime=True, SkipAppearance=True, SkipTrueTone=True,
            SkipUnlockWithWatch=True))],
        scope="System", note="ADE skip keys are set in the Intune enrollment profile.")

profile(F, "printing", "Printing",
        "Requires admin to add printers and allows local printers.",
        [("com.apple.mcxprinting", "Printing", dict(
            AllowLocalPrinters=True, RequireAdminToAddPrinters=True,
            ShowOnlyManagedPrinters=False, PrintFooter=False))])

profile(F, "login-window-security", "Login Window - Banner and Security",
        "Legal banner, shows name and password fields, disables auto-login, console login and FDE auto-login.",
        [("com.apple.loginwindow", "Login window", dict(
            LoginwindowText="Authorised use only. Activity may be monitored.",
            SHOWFULLNAME=True, DisableFDEAutoLogin=True, DisableConsoleAccess=True,
            HideAdminUsers=True, **{"com.apple.login.mcx.DisableAutoLoginClient": True}))],
        note="Complements the existing Login Windows Settings profile in the repo root.")

profile(F, "finder-settings", "Finder Settings",
        "Shows external/removable media and mounted servers on the desktop; hides internal disks.",
        [("com.apple.finder", "Finder", dict(
            ShowHardDrivesOnDesktop=False, ShowExternalHardDrivesOnDesktop=True,
            ShowMountedServersOnDesktop=True, ShowRemovableMediaOnDesktop=True,
            ProhibitConnectTo=False, WarnOnEmptyTrash=True))],
        scope="User", note="User channel.")

profile(F, "safari-settings", "Safari Settings",
        "Home page, full URL display and safe defaults. macOS 26 also supports declarative Safari configuration for bookmarks, start page and summaries.",
        [("com.apple.Safari", "Safari", dict(
            HomePage="https://intranet.example.com", ShowFullURLInSmartSearchField=True,
            AutoOpenSafeDownloads=False, SendDoNotTrackHTTPHeader=True))],
        scope="User", note="User channel - edit HomePage.")

# ===========================================================================
# 06 - Privacy (PPPC)
# ===========================================================================
F = "06-privacy-pppc"


def tcc_entry(ident, team, auth, comment):
    return dict(Identifier=ident, IdentifierType="bundleID",
                CodeRequirement=code_req(ident, team), StaticCode=False,
                Authorization=auth, Comment=comment)


# --- Per-app "full permissions" PPPC profiles -------------------------------
# What MDM can and cannot grant (Apple TCC payload schema):
#   Allow ............ file/folder services, Accessibility*, PostEvent, Contacts, Calendar,
#                      Reminders, Photos, MediaLibrary, FileProviderPresence, App Bundles/Data
#   AllowStandardUserToSetSystemService ... ScreenCapture, ListenEvent (users approve w/o admin)
#   Deny only ........ Camera, Microphone (cannot be pre-approved; users get a one-time prompt)
#   *Accessibility, Camera, Microphone, SpeechRecognition, BluetoothAlways are deprecated in 27.
# Set INCLUDE_ACCESSIBILITY = False to drop Accessibility/PostEvent (avoids the per-app
# notification macOS 27 shows for pushed Accessibility grants).
INCLUDE_ACCESSIBILITY = True

CHROME_TEAM = "EQHXZ8M8AV"
MOZILLA_TEAM = "43AQ936H96"
ANTHROPIC_TEAM = "Q6L2SF6YDW"

FULL_ALLOW = [
    "SystemPolicyAllFiles", "SystemPolicySysAdminFiles",
    "SystemPolicyDesktopFolder", "SystemPolicyDocumentsFolder",
    "SystemPolicyDownloadsFolder", "SystemPolicyNetworkVolumes",
    "SystemPolicyRemovableVolumes", "SystemPolicyAppBundles", "SystemPolicyAppData",
    "FileProviderPresence", "MediaLibrary",
    "AddressBook", "Calendar", "Reminders", "Photos",
]
ACCESSIBILITY_ALLOW = ["Accessibility", "PostEvent"]
STD_USER_SET = ["ScreenCapture", "ListenEvent"]


def services_for(apps):
    """apps: list of (bundle_id, team, comment). Returns the Services dict."""
    svc = {}
    allow = FULL_ALLOW + (ACCESSIBILITY_ALLOW if INCLUDE_ACCESSIBILITY else [])
    for name in allow:
        svc[name] = [tcc_entry(b, t, "Allow", c) for b, t, c in apps]
    for name in STD_USER_SET:
        svc[name] = [tcc_entry(b, t, "AllowStandardUserToSetSystemService", c) for b, t, c in apps]
    return svc


def pppc(slug, title, apps, note="", extra_desc=""):
    profile(F, slug, title,
            f"PPPC grants for: {', '.join(c for _, _, c in apps)}. Grants every service MDM is allowed to "
            "pre-approve (files/folders, Contacts, Calendar, Reminders, Photos, Accessibility, input events); "
            "Screen Recording and Input Monitoring are set so standard users can approve without admin. "
            "Camera and Microphone cannot be pre-approved by MDM. " + extra_desc,
            [("com.apple.TCC.configuration-profile-policy", "Privacy Preferences", dict(
                Services=services_for(apps)))],
            os27="Yes (Accessibility deprecated)",
            note=note or "Verify code requirement with codesign -dr -.")


pppc("pppc-google-chrome", "PPPC - Google Chrome",
     [("com.google.Chrome", CHROME_TEAM, "Google Chrome")])
pppc("pppc-microsoft-edge", "PPPC - Microsoft Edge",
     [("com.microsoft.edgemac", MS_TEAM, "Microsoft Edge")])
pppc("pppc-mozilla-firefox", "PPPC - Mozilla Firefox",
     [("org.mozilla.firefox", MOZILLA_TEAM, "Mozilla Firefox")])
pppc("pppc-microsoft-teams", "PPPC - Microsoft Teams",
     [("com.microsoft.teams2", MS_TEAM, "Microsoft Teams (new)"),
      ("com.microsoft.teams", MS_TEAM, "Microsoft Teams (classic)")],
     note="Covers new Teams and the retired classic client.")
pppc("pppc-zoom", "PPPC - Zoom Workplace",
     [("us.zoom.xos", ZOOM_TEAM, "Zoom Workplace")])
pppc("pppc-microsoft-office", "PPPC - Microsoft Office (Word, Excel, PowerPoint, Outlook, OneNote)",
     [("com.microsoft.Word", MS_TEAM, "Microsoft Word"),
      ("com.microsoft.Excel", MS_TEAM, "Microsoft Excel"),
      ("com.microsoft.Powerpoint", MS_TEAM, "Microsoft PowerPoint"),
      ("com.microsoft.Outlook", MS_TEAM, "Microsoft Outlook"),
      ("com.microsoft.onenote.mac", MS_TEAM, "Microsoft OneNote")])
pppc("pppc-microsoft-onedrive", "PPPC - Microsoft OneDrive",
     [("com.microsoft.OneDrive", MS_TEAM, "Microsoft OneDrive")])
pppc("pppc-microsoft-defender", "PPPC - Microsoft Defender for Endpoint",
     [("com.microsoft.wdav", MS_TEAM, "Defender (wdav)"),
      ("com.microsoft.wdav.epsext", MS_TEAM, "Defender Endpoint Security extension"),
      ("com.microsoft.dlp.daemon", MS_TEAM, "Defender Endpoint DLP daemon"),
      ("com.microsoft.dlp.agent", MS_TEAM, "Defender Endpoint DLP agent")],
     note="Also deploy the Defender system extension, network filter and notification profiles (repo root).",
     extra_desc="Does not approve the system/network extensions; those need their own profiles.")
pppc("pppc-claude-desktop", "PPPC - Claude Desktop",
     [("com.anthropic.claudefordesktop", ANTHROPIC_TEAM, "Claude Desktop")],
     note="Claude Code (CLI) runs inside Terminal/IDE; grant those separately.")

profile(F, "pppc-template", "PPPC (template)",
        "Template. Full Disk Access for one app via Team ID. Replace identifier, Team ID and code requirement. Avoid Accessibility; it is deprecated in macOS 27.",
        [("com.apple.TCC.configuration-profile-policy", "Privacy", dict(
            Services=dict(SystemPolicyAllFiles=[
                tcc_entry("com.example.app", "REPLACE_TEAMID", "Allow",
                          "Example app")])))],
        os27="Yes (deprecated keys)",
        note="PPPC keys deprecated in 27 but still work through the 27 cycle.")

# ===========================================================================
# Legacy (macOS 26 only)
# ===========================================================================
F = "legacy-macos-26-only"

profile(F, "softwareupdate-legacy", "Software Update (legacy, macOS 26 only)",
        "Legacy com.apple.SoftwareUpdate payload and restriction deferrals. REMOVED in macOS 27 - they do nothing there. Use Declarative Device Management (com.apple.configuration.softwareupdate.settings and enforcement) via Intune's Settings catalog for macOS 27.",
        [("com.apple.SoftwareUpdate", "Software Update", dict(
            AutomaticCheckEnabled=True, AutomaticDownload=True,
            AutomaticallyInstallMacOSUpdates=False, CriticalUpdateInstall=True,
            ConfigDataInstall=True, AllowPreReleaseInstallation=False)),
         ("com.apple.applicationaccess", "Update deferrals", dict(
             forceDelayedSoftwareUpdates=True, enforcedSoftwareUpdateDelay=14,
             enforcedSoftwareUpdateMajorOSDeferredInstallDelay=30,
             enforcedSoftwareUpdateMinorOSDeferredInstallDelay=7))],
        os27="No (removed)", note="Removed in macOS 27.0. Use DDM.")

profile(F, "restrictions-apple-intelligence", "Restrictions - Apple Intelligence (legacy keys)",
        "Disables Apple Intelligence features using com.apple.applicationaccess keys. Deprecated in macOS 26.4 in favour of declarative configurations; macOS 27 adds a Siri AI restriction in the declarative model only.",
        [("com.apple.applicationaccess", "Apple Intelligence", dict(
            allowWritingTools=False, allowImagePlayground=False, allowGenmoji=False,
            allowMailSummary=False, allowNotesTranscriptionSummary=False,
            allowSafariSummary=False, allowExternalIntelligenceIntegrations=False))],
        os27="Deprecated", note="Deprecated 26.4. Verify keys against Apple's schema.")

# ===========================================================================
# 07 - Browsers (aligned with CIS Benchmark themes)
# ===========================================================================
# NOTE: the CIS Chrome and Edge benchmarks are written for Windows/Group Policy and the
# Firefox benchmark for ESR/GPO; there is no macOS-specific edition. These profiles map the
# recommended *policy settings* to macOS managed preferences. They are not CIS certified.
# Level 2 profiles are a SUPERSET of Level 1 - assign one or the other, never both.
F = "07-browsers"
MATRIX = {}  # browser -> {policy: (l1, l2)}

_CHROME_L1 = {
    "ExtensionInstallBlocklist": ["*"],
    "ExtensionInstallAllowlist": [],            # add approved extension IDs
    "BlockExternalExtensions": True,
    "SafeBrowsingProtectionLevel": 1,
    "DisableSafeBrowsingProceedAnyway": True,
    "BlockThirdPartyCookies": True,
    "SitePerProcess": True,
    "EnableDoNotTrack": True,
    "SSLVersionMin": "tls1.2",
    "DnsOverHttpsMode": "automatic",
    "DefaultPopupsSetting": 2,
    "DefaultGeolocationSetting": 3,
    "DefaultInsecureContentSetting": 2,
    "DefaultFileSystemWriteGuardSetting": 2,
    "BasicAuthOverHttpEnabled": False,
    "AllowCrossOriginAuthPrompt": False,
    "EnableMediaRouter": False,
    "DownloadRestrictions": 1,
    "PasswordLeakDetectionEnabled": True,
    "AutofillCreditCardEnabled": False,
    "RelaunchNotification": 2,
    "RelaunchNotificationPeriod": 604800000,
    "MetricsReportingEnabled": False,
}
_CHROME_L2 = {
    "SafeBrowsingProtectionLevel": 2,
    "DefaultGeolocationSetting": 2,
    "DownloadRestrictions": 2,
    "PasswordManagerEnabled": False,
    "AutofillAddressEnabled": False,
    "SpellCheckServiceEnabled": False,
    "SyncDisabled": True,
    "BrowserSignin": 0,
}

_EDGE_L1 = {
    "ExtensionInstallBlocklist": ["*"],
    "ExtensionInstallAllowlist": [],
    "BlockExternalExtensions": True,
    "SmartScreenEnabled": True,
    "SmartScreenPuaEnabled": True,
    "PreventSmartScreenPromptOverride": True,
    "PreventSmartScreenPromptOverrideForFiles": True,
    "TyposquattingCheckerEnabled": True,
    "EnhanceSecurityMode": 1,
    "BlockThirdPartyCookies": True,
    "SitePerProcess": True,
    "SSLVersionMin": "tls1.2",
    "DnsOverHttpsMode": "automatic",
    "DefaultPopupsSetting": 2,
    "DefaultGeolocationSetting": 2,
    "DefaultInsecureContentSetting": 2,
    "DefaultFileSystemWriteGuardSetting": 2,
    "DefaultAutomaticDownloadsSetting": 2,
    "BasicAuthOverHttpEnabled": False,
    "AllowCrossOriginAuthPrompt": False,
    "GuidedSwitchEnabled": False,
    "EnableMediaRouter": False,
    "DownloadRestrictions": 1,
    "TrackingPrevention": 2,
    "DiagnosticData": 1,
    "HideFirstRunExperience": True,
    "RelaunchNotification": 2,
    "RelaunchNotificationPeriod": 604800000,
}
_EDGE_L2 = {
    "EnhanceSecurityMode": 2,
    "TrackingPrevention": 3,
    "DownloadRestrictions": 2,
    "DiagnosticData": 0,
    "PasswordManagerEnabled": False,
    "PaymentMethodQueryEnabled": False,
    "NetworkPredictionOptions": 2,
    "PersonalizationReportingEnabled": False,
    "EdgeShoppingAssistantEnabled": False,
    "SyncDisabled": True,
}

_FF_L1 = {
    "EnterprisePoliciesEnabled": True,
    "DisableTelemetry": True,
    "DisableFirefoxStudies": True,
    "DisablePocket": True,
    "DisableFeedbackCommands": True,
    "DontCheckDefaultBrowser": True,
    "DisableAppUpdate": False,
    "AppAutoUpdate": True,
    "BlockAboutConfig": True,
    "DisableSafeMode": True,
    "SSLVersionMin": "tls1.2",
    "HttpsOnlyMode": "enabled",
    "AutofillCreditCardEnabled": False,
    "InstallAddonsPermission": {"Default": False},
    "ExtensionSettings": {"*": {"installation_mode": "blocked",
                                "blocked_install_message": "Extensions are restricted by IT policy."}},
    "PopupBlocking": {"Default": True, "Locked": True},
    "Cookies": {"Behavior": "reject-tracker-and-partition-foreign", "Locked": True},
    "EnableTrackingProtection": {"Value": True, "Locked": True, "Cryptomining": True,
                                 "Fingerprinting": True, "EmailTracking": True},
    "DNSOverHTTPS": {"Enabled": True, "Locked": True},
    "FirefoxSuggest": {"WebSuggestions": False, "SponsoredSuggestions": False,
                       "ImproveSuggest": False, "Locked": True},
    "UserMessaging": {"WhatsNew": False, "ExtensionRecommendations": False,
                      "FeatureRecommendations": False, "UrlbarInterventions": False,
                      "SkipOnboarding": True, "MoreFromMozilla": False, "Locked": True},
}
_FF_L2 = {
    "HttpsOnlyMode": "force_enabled",
    "PasswordManagerEnabled": False,
    "OfferToSaveLogins": False,
    "AutofillAddressEnabled": False,
    "DisableFormHistory": True,
    "DisableFirefoxAccounts": True,
    "NetworkPrediction": False,
    "SearchSuggestEnabled": False,
    "BlockAboutProfiles": True,
    "Cookies": {"Behavior": "reject-foreign", "Locked": True},
    "Permissions": {"Location": {"BlockNewRequests": True, "Locked": True},
                    "Camera": {"BlockNewRequests": True, "Locked": True},
                    "Microphone": {"BlockNewRequests": True, "Locked": True},
                    "Notifications": {"BlockNewRequests": True, "Locked": True}},
    "SanitizeOnShutdown": {"Cache": True, "Cookies": True, "Downloads": True,
                           "FormData": True, "History": True, "Sessions": True,
                           "OfflineApps": True, "Locked": True},
    "GenerativeAI": {"Enabled": False, "Locked": True},
}

_BROWSERS = [
    ("chrome", "Google Chrome", "com.google.Chrome", _CHROME_L1, _CHROME_L2,
     "Update policy (Keystone) and Chrome Browser Cloud Management are not set here. "
     "AllowOutdatedPlugins is obsolete and omitted. Add approved IDs to ExtensionInstallAllowlist."),
    ("edge", "Microsoft Edge", "com.microsoft.Edge", _EDGE_L1, _EDGE_L2,
     "GamerModeEnabled and LinkedAccountEnabled are obsolete and omitted. Add approved IDs to "
     "ExtensionInstallAllowlist. Confirm in edge://policy."),
    ("firefox", "Mozilla Firefox", "org.mozilla.firefox", _FF_L1, _FF_L2,
     "Blocks all extensions by default (ExtensionSettings). Add allowed add-on IDs. "
     "Confirm in about:policies."),
]

for slug, label, domain, l1, l2, extra in _BROWSERS:
    l2_full = {**l1, **l2}
    MATRIX[label] = {k: (l1.get(k), l2_full.get(k)) for k in sorted(l2_full)}
    for lvl, content in (("level1", l1), ("level2", l2_full)):
        tag = "Level 1" if lvl == "level1" else "Level 2 (superset of Level 1)"
        profile(F, f"{slug}-cis-{lvl}", f"{label} - CIS-aligned {tag}",
                f"{label} managed preferences aligned with CIS Benchmark recommendations ({tag}). "
                "CIS publishes these benchmarks for Windows/GPO; settings are translated to macOS here. "
                "Not CIS certified. "
                + ("Assign this OR the Level 1 profile, not both." if lvl == "level2" else
                   "Assign this OR the Level 2 profile, not both."),
                [(domain, f"{label} policies", dict(content))],
                note=extra if lvl == "level1" else "Superset of Level 1.")


def write_matrix():
    lines = ["# Browser policy matrix (CIS-aligned)", "",
             "Generated by `tools/generate.py`. Level 2 profiles include every Level 1 setting "
             "plus the overrides/additions shown. Complex values are shown as JSON.", ""]
    import json
    for label, rows in MATRIX.items():
        lines += [f"## {label}", "", "| Policy | Level 1 | Level 2 |", "|---|---|---|"]
        for k, (a, b) in rows.items():
            fa = "not set" if a is None else f"`{json.dumps(a)}`"
            fb = "not set" if b is None else f"`{json.dumps(b)}`"
            lines.append(f"| `{k}` | {fa} | {fb} |")
        lines.append("")
    (ROOT / "07-browsers" / "POLICY-MATRIX.md").write_text("\n".join(lines))


# ===========================================================================
# README table
# ===========================================================================
def build_readme_table():
    rows = ["| Folder | File | Name | Scope | macOS 26 | macOS 27 | Notes |",
            "|---|---|---|---|---|---|---|"]
    for s in sorted(SPECS, key=lambda x: (x["folder"], x["file"])):
        rows.append(f"| {s['folder']} | `{s['file']}` | {s['title']} | {s['scope']} | "
                    f"{s['os26']} | {s['os27']} | {s['note']} |")
    return "\n".join(rows)


if __name__ == "__main__":
    table = build_readme_table()
    readme = ROOT / "README.md"
    start, end = "<!-- TABLE:START -->", "<!-- TABLE:END -->"
    text = readme.read_text()
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    readme.write_text(f"{head}{start}\n{table}\n{end}{tail}")
    write_matrix()
    print(f"Generated {len(SPECS)} profiles")
