| Folder | File | Name | Scope | macOS 26 | macOS 27 | Notes |
|---|---|---|---|---|---|---|
| 01-security | `filevault-enable-no-escrow.mobileconfig` | FileVault - Enable (no escrow) | System | Yes | Yes | Lab/testing only. Use native Intune FileVault policy for key escrow. |
| 01-security | `firewall.mobileconfig` | Firewall | System | Yes | Yes |  |
| 01-security | `gatekeeper.mobileconfig` | Gatekeeper | System | Yes | Yes |  |
| 01-security | `local-accounts-no-guest.mobileconfig` | Local Accounts - Disable Guest | System | Yes | Yes |  |
| 01-security | `passcode-policy.mobileconfig` | Passcode Policy | System | Yes | Yes | Set maxPINAgeInDays > 0 only if you want forced rotation. |
| 01-security | `screensaver-lock.mobileconfig` | Screen Saver and Lock | User | Yes | Yes | Deploy to the user channel in Intune. |
| 01-security | `smartcard.mobileconfig` | Smart Card Policy | System | Yes | Yes |  |
| 02-restrictions | `appstore-restrictions.mobileconfig` | App Store Restrictions | System | Yes | Yes |  |
| 02-restrictions | `restrictions-diagnostics-ads.mobileconfig` | Restrictions - Diagnostics and Ads | System | Yes | Yes |  |
| 02-restrictions | `restrictions-hardening.mobileconfig` | Restrictions - Hardening | System | Yes | Yes |  |
| 02-restrictions | `restrictions-icloud.mobileconfig` | Restrictions - iCloud | System | Yes | Yes |  |
| 02-restrictions | `web-content-filter-builtin.mobileconfig` | Web Content Filter (built-in) | System | Yes | Yes | Edit DenyListURLs. Safari only; use a vendor content filter for other browsers. |
| 03-network | `dns-over-https.mobileconfig` | DNS over HTTPS (template) | System | Yes | Yes | Template - macOS 27 adds declarative DNS; this payload remains supported. |
| 03-network | `ethernet-8021x.mobileconfig` | Ethernet - 802.1X EAP-TLS (template) | System | Yes | Yes | Template - verify against your NAC. Native Intune wired profile recommended. |
| 03-network | `vpn-ikev2.mobileconfig` | VPN - IKEv2 (template) | System | Yes | Yes | Template - edit server/identities; add a cert payload. |
| 03-network | `wifi-eap-tls.mobileconfig` | Wi-Fi - EAP-TLS with SCEP (template) | System | Yes | Yes | Template - SCEP and RADIUS values required. |
| 03-network | `wifi-wpa2-personal.mobileconfig` | Wi-Fi - WPA2 Personal (template) | System | Yes | Yes | Template - edit SSID/password. |
| 04-identity | `domains-autofill.mobileconfig` | Managed Domains (template) | System | Yes | Yes | Template - edit domains. |
| 04-identity | `entra-enterprise-sso-redirect.mobileconfig` | Microsoft Entra - Enterprise SSO Plug-in | System | Yes | Yes | Company Portal must be installed first. |
| 04-identity | `entra-platform-sso.mobileconfig` | Microsoft Entra - Platform SSO (Secure Enclave) | System | Yes | Yes | Prefer Intune Settings catalog for new Platform SSO keys. |
| 04-identity | `scep-certificate.mobileconfig` | SCEP Certificate (template) | System | Yes | Yes | Template. See tools/make-root-cert-profile.py for trusted root profiles. |
| 05-system-apps | `finder-settings.mobileconfig` | Finder Settings | User | Yes | Yes | User channel. |
| 05-system-apps | `login-window-security.mobileconfig` | Login Window - Banner and Security | System | Yes | Yes | Complements the existing Login Windows Settings profile in the repo root. |
| 05-system-apps | `managed-login-items-microsoft.mobileconfig` | Managed Login Items - Microsoft | System | Yes | Yes |  |
| 05-system-apps | `managed-login-items-template.mobileconfig` | Managed Login Items (template) | System | Yes | Yes | Template - edit rules. |
| 05-system-apps | `printing.mobileconfig` | Printing | System | Yes | Yes |  |
| 05-system-apps | `safari-settings.mobileconfig` | Safari Settings | User | Yes | Yes | User channel - edit HomePage. |
| 05-system-apps | `setup-assistant-skip.mobileconfig` | Setup Assistant - Skip Panes | System | Yes | Yes | ADE skip keys are set in the Intune enrollment profile. |
| 05-system-apps | `system-extensions-template.mobileconfig` | System Extensions (template) | System | Yes | Yes | Template - edit Team ID/bundle IDs. |
| 06-privacy-pppc | `pppc-teams-screen-sharing.mobileconfig` | PPPC - Teams and Zoom Screen Recording | System | Yes | Yes (no Accessibility) | Avoid Accessibility service entries - deprecated in macOS 27. |
| 06-privacy-pppc | `pppc-template.mobileconfig` | PPPC (template) | System | Yes | Yes (deprecated keys) | PPPC keys deprecated in 27 but still work through the 27 cycle. |
| legacy-macos-26-only | `restrictions-apple-intelligence.mobileconfig` | Restrictions - Apple Intelligence (legacy keys) | System | Yes | Deprecated | Deprecated 26.4. Verify keys against Apple's schema. |
| legacy-macos-26-only | `softwareupdate-legacy.mobileconfig` | Software Update (legacy, macOS 26 only) | System | Yes | No (removed) | Removed in macOS 27.0. Use DDM. |
