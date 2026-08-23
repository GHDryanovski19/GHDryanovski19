<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Georgi Dryanovski — full stack engineer. Frontend architecture, design systems, release pipelines." src="assets/banner-light.svg" width="100%">
</picture>

**Georgi Dryanovski** — Software Engineer at Verasoft Labs, Burgas, Bulgaria
[LinkedIn](https://www.linkedin.com/in/georgi-dryanovski-896072230/) · [Email](mailto:georgidrianovski@abv.bg) · [inkblotstudio.eu](https://inkblotstudio.eu)

---

## What I do

Six years building products end to end, with the centre of gravity on the frontend: design
systems, application architecture, and the release pipeline that puts them in front of users.

The work I take on is usually bigger than one screen — an ERP that replaces five separate
tools, a component library four products depend on, one codebase that ships to web, iOS,
Android and desktop. I optimise for two things: interfaces that stay fast on real data
volumes, and code the next engineer can change without asking me first.

**Right now** — frontend architecture and releases at Verasoft Labs, and building Citron,
an AI native business operating system, through my own studio.

---

## Design systems, published and versioned

Three libraries I designed, built and maintain. All three are on npm and consumed in
production by shipping products, not demos.

| Package | | What it is |
| --- | --- | --- |
| [`@citron-systems/citron-ds`](https://www.npmjs.com/package/@citron-systems/citron-ds) | `v2.0` | Token system built on Style Dictionary. One source of truth compiles to CSS custom properties, SCSS, JS and a machine readable JSON reference, and ships self hosted fonts, motion tokens and brand assets alongside it. MIT. [Source](https://github.com/Inkblot-Studio/citron-ds) |
| [`@citron-systems/citron-ui`](https://www.npmjs.com/package/@citron-systems/citron-ui) | `v1.26` | Accessible, token driven React component library — the shared UI layer under every Citron product. |
| [`@nexcomponent/lib`](https://www.npmjs.com/package/@nexcomponent/lib) | `v2.7` | React UI library, shipped as parallel ESM and CJS builds with generated type declarations. [Source](https://github.com/Inkblot-Studio/nexcomponent-ui) |

The components are the easy part. The value is in the contract: consumers reference
*semantic* tokens, never raw values, so a rebrand is a token rebuild rather than a find and
replace across four repositories — and a contrast fix lands everywhere at once.

---

## Selected work

### Citron — AI native business operating system

Replaces a business's separate CRM, sales, finance, inventory and operations tools with one
system: invoicing, analytics, an assistant layer, and a restaurant POS module.

A modular service layer over a normalised schema with role based access across user tiers,
and a React frontend built entirely on the shared component library above. The POS is
offline first — orders and reservations are written locally and reconciled by a sync layer,
because a restaurant does not stop taking orders when the network does.

<sub>React · TypeScript · Node.js · .NET · SQL Server</sub>

### KORVUE and FitVue — one codebase, four targets

Commercial platforms at Verasoft Labs shipping to web, iOS, Android and desktop from a
single shared codebase. I lead architecture and development and own the release process end
to end — build configuration, store submissions, versioning and rollout.

<sub>TypeScript · Ionic · Capacitor · Electron</sub>

### Inkblot Studio — studio site and WebGL work

My studio's site: a GPU fluid simulation of black ink on paper as the homepage hero,
draining into a projects gallery on scroll. Three.js with a WebGL worker layout and custom
GLSL, GSAP for motion, React 19 on Vite.

Deliberately no Tailwind and no component framework — the entire visual layer is a hand
built token system, which is what let the hero stay inside its performance budget on
mid range hardware.

<sub>React 19 · Three.js · GLSL · GSAP · Vite</sub>

### Educational game platform

Web delivered learning games built for the Polish education system. I led the development
team and owned delivery.

<sub>JavaScript · Unity · WebGL</sub>

---

## How I work

**Tokens before components.** A design system that exposes raw hex values has already
failed; the abstraction is the deliverable.

**Performance is a budget, not a phase.** Numbers get set before the first commit and the
build fails when they are missed — that is the only version of this that survives a deadline.

**Offline and failure states are part of the feature.** The network drops, the request
times out, the tab is restored from three days ago. If that path is undesigned, the feature
is not finished.

**Whoever writes it, ships it.** I own releases for what I build. Owning the pipeline is
what keeps the architecture honest.

**Readable beats clever.** The next engineer to open the file might be me in eight months,
with none of the context.

---

## Stack

**Daily** — TypeScript · React · Node.js · Sass · Vite · Storybook · Style Dictionary

**Also shipped with** — .NET and C# · SQL Server · Express · Angular · Redux · Three.js and
GLSL · Ionic, Capacitor and Electron · Flutter · Firebase · AWS and Vercel · GitHub Actions

**Adjacent** — Figma, and enough of the Adobe suite to produce my own assets rather than
wait on them.

---

## Elsewhere

[LinkedIn](https://www.linkedin.com/in/georgi-dryanovski-896072230/) ·
[Inkblot Studio](https://inkblotstudio.eu) ·
[Citron](https://citronos.com) ·
[npm](https://www.npmjs.com/package/@citron-systems/citron-ds)

Bulgarian native, English C1, German A2. Open to senior frontend and full stack roles, and
always up for a conversation about design systems or a rendering problem that should not be
this hard.
