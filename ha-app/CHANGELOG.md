# Changelog

## 0.2.0

The family and its devices.

- A first-run screen creates the first adult, with a PIN and a password.
- The rest of the family is added in the management pages, each with a face photo or a
  coloured initial.
- A new phone, tablet or PC is allowed once by an adult's PIN and then opens the app
  without asking. Devices can be renamed and removed in the management pages.
- After five wrong PINs in a row, PIN entry pauses, longer after each further wrong try.

After updating, the app shows the first-run screen once. Tasks arrive with the next
version.

## 0.1.1

Fixed: the page did not open under a name such as `homeassistant.local`, only under the
numeric IPv4 address. The app now answers over IPv6 as well.

## 0.1.0

First installable version. It shows a test page in Czech and English that confirms the
whole chain works: the page, its styles, live refresh, and the database.
