<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Georgi Dryanovski — full stack engineer. Frontend architecture, design systems, release pipelines." src="assets/banner-light.svg" width="100%">
</picture>

**Georgi Dryanovski** — Software Engineer at Verasoft Labs, Burgas, Bulgaria
[LinkedIn](https://www.linkedin.com/in/georgi-dryanovski-896072230/) · [Email](mailto:georgidrianovski@abv.bg)

---

## What I do

Five plus years building products end to end, with the centre of gravity on the frontend.
At **Verasoft Labs** I lead frontend architecture and development across the company's
commercial products, and own the release process that puts them in front of users.

I optimise for two things: interfaces that stay fast on real data volumes, and code the
next engineer can change without asking me first.

---

## At Verasoft Labs

<table>
<tr>
<td width="34%" valign="top">

**Multi platform product engineering**

</td>
<td valign="top">

**KORVUE** and **FitVue** — commercial platforms shipping to web, mobile and desktop from a
single shared codebase. I lead architecture and development: the module boundaries, the
shared state and data layer, and the platform seams where one codebase has to behave
natively on four targets.

<sub><kbd>TypeScript</kbd> <kbd>Ionic</kbd> <kbd>Capacitor</kbd> <kbd>Electron</kbd></sub>

</td>
</tr>
<tr>
<td valign="top">

**Release ownership**

</td>
<td valign="top">

I own releases end to end for what I build — build configuration per target, versioning,
store submission and rollout. Owning the pipeline is what keeps the architecture honest;
an abstraction that makes shipping harder gets found in the first release, not the fourth.

<sub><kbd>GitHub Actions</kbd> <kbd>Git</kbd></sub>

</td>
</tr>
<tr>
<td valign="top">

**Documentation platform**

</td>
<td valign="top">

A multi brand documentation site serving both products from one codebase — per brand
theming and environment driven builds, a shared MDX component layer, a generated client
side search index, and content authored in a headless CMS rather than committed as files.

<sub><kbd>Docusaurus</kbd> <kbd>React</kbd> <kbd>Sass</kbd> <kbd>Sanity</kbd></sub>

</td>
</tr>
</table>

---

## Libraries I maintain

Three React and design token libraries I designed, built and publish to npm. All are
versioned, consumed by shipping applications, and open to read.

[![citron-ds](https://img.shields.io/npm/v/@citron-systems/citron-ds?style=flat-square&label=%40citron-systems%2Fcitron-ds&labelColor=dcd8d1&color=14120f)](https://www.npmjs.com/package/@citron-systems/citron-ds)
[![citron-ui](https://img.shields.io/npm/v/@citron-systems/citron-ui?style=flat-square&label=%40citron-systems%2Fcitron-ui&labelColor=dcd8d1&color=14120f)](https://www.npmjs.com/package/@citron-systems/citron-ui)
[![nexcomponent](https://img.shields.io/npm/v/@nexcomponent/lib?style=flat-square&label=%40nexcomponent%2Flib&labelColor=dcd8d1&color=14120f)](https://www.npmjs.com/package/@nexcomponent/lib)

| Package | What it is |
| --- | --- |
| **`citron-ds`** | A design token system built on Style Dictionary. One source of truth compiles to CSS custom properties, SCSS, JS and a machine readable JSON reference, and ships self hosted fonts and motion tokens alongside it. MIT licensed. |
| **`citron-ui`** | An accessible, token driven React component library — the shared UI layer beneath the applications below. |
| **`@nexcomponent/lib`** | A React UI library shipped as parallel ESM and CJS builds with generated type declarations. |

The components are the easy part. The value is in the contract: consumers reference
*semantic* tokens, never raw values, so a rebrand becomes a token rebuild rather than a
find and replace across four repositories, and a contrast fix lands everywhere at once.

---

## Independent projects

**A modular business platform** — CRM, sales, finance, inventory and operations in one
system, over a normalised schema with role based access across user tiers. Includes a point
of sale module that is offline first: orders and reservations are written locally and
reconciled by a sync layer, because a restaurant does not stop taking orders when the
network does.

<sub><kbd>React</kbd> <kbd>TypeScript</kbd> <kbd>Node.js</kbd> <kbd>.NET</kbd> <kbd>SQL Server</kbd></sub>

**Real time WebGL** — a scroll driven GPU fluid simulation rendered with custom GLSL and a
worker based scene layout, built to hold its frame budget on mid range hardware. The whole
visual layer is a hand built token system, no utility framework.

<sub><kbd>Three.js</kbd> <kbd>GLSL</kbd> <kbd>GSAP</kbd> <kbd>React 19</kbd> <kbd>Vite</kbd></sub>

**Earlier** — led the development team on a web delivered educational game platform built
for the Polish education system.

<sub><kbd>JavaScript</kbd> <kbd>Unity</kbd> <kbd>WebGL</kbd></sub>

---

## How I work

> **Tokens before components.** A design system that exposes raw hex values has already
> failed. The abstraction is the deliverable.

> **Performance is a budget, not a phase.** Numbers get set before the first commit and the
> build fails when they are missed. That is the only version of this that survives a deadline.

> **Offline and failure states are part of the feature.** The network drops, the request
> times out, the tab is restored from three days ago. If that path is undesigned, the
> feature is not finished.

> **Readable beats clever.** The next engineer to open the file might be me in eight months,
> with none of the context.

---

## Stack

**Daily** <kbd>TypeScript</kbd> <kbd>React</kbd> <kbd>Node.js</kbd> <kbd>Sass</kbd> <kbd>Vite</kbd> <kbd>Storybook</kbd> <kbd>Style&nbsp;Dictionary</kbd>

**Also shipped with** <kbd>.NET</kbd> <kbd>C#</kbd> <kbd>SQL&nbsp;Server</kbd> <kbd>Express</kbd> <kbd>Angular</kbd> <kbd>Redux</kbd> <kbd>Three.js</kbd> <kbd>GLSL</kbd> <kbd>Ionic</kbd> <kbd>Capacitor</kbd> <kbd>Electron</kbd> <kbd>Flutter</kbd> <kbd>Firebase</kbd> <kbd>AWS</kbd> <kbd>Vercel</kbd>

**Adjacent** <kbd>Figma</kbd> — and enough of the Adobe suite to produce my own assets rather than wait on them.

---

<sub>Bulgarian native · English C1 · German A2</sub>

Always up for a conversation about design systems, frontend architecture, or a rendering
problem that should not be this hard.
