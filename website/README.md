# 🌐 ISHA Web Portal — Production Frontend

> The official interactive dashboard, statistics gallery, and landing platform for **ISHA (Iterative Software Harness & Arbitrator)**.
> Live at [**https://isha-ai.vercel.app**](https://isha-ai.vercel.app) (mirror: [https://isha-agent.vercel.app](https://isha-agent.vercel.app)).

[![React 19](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-blue.svg)](https://typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg)](https://vitejs.dev)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.3-38B2AC.svg)](https://tailwindcss.com)
[![Framer Motion](https://img.shields.io/badge/Framer_Motion-14.0-black.svg)](https://motion.dev)
[![Deployment: Vercel](https://img.shields.io/badge/Deploy-Vercel-black.svg)](https://vercel.com)

---

## 📂 Clean Project Directory Map

```text
website/
├── src/                          # Application Source Code
│   ├── components/               # React UI Components
│   │   ├── Main.tsx              # Primary view wrapper & layout container
│   │   ├── Preloader_002.tsx     # Smooth entrance preloader animation
│   │   │
│   │   └── v1/                   # Modular Hero, Sections & Skiper UI Blocks
│   │       ├── AboutSection.tsx      # Problem statement & mission overview
│   │       ├── AddGitRepoCard.tsx    # Interactive repo input & benchmark runner card
│   │       ├── CliSection.tsx        # Terminal demo & CLI command walkthrough
│   │       ├── StatsSection.tsx      # Verified benchmark metrics container
│   │       ├── StatsSection.content.tsx # Audited SWE-bench Lite data payloads
│   │       │
│   │       └── skiper*.tsx           # Premium interactive UI blocks:
│   │           ├── skiper29.tsx      # Terminal command runner & prompt simulator
│   │           ├── skiper35.tsx      # Mobile-responsive audited metric accordion
│   │           ├── skiper82.tsx      # Animated benchmark comparison graph & charts
│   │           ├── skiper13.tsx      # Bento grid feature spotlight
│   │           ├── skiper16.tsx      # Minimal diff code viewer
│   │           └── skiper52.tsx      # Live agent trajectory feed
│   │
│   ├── pages/                    # High-Level Page Views
│   ├── lib/                      # Shared Frontend Utilities
│   │   └── utils.ts              # `cn()` clsx + tailwind-merge helper
│   ├── utils/                    # Additional Formatters & Math Helpers
│   ├── assets/                   # Static Images, Badges, and Logos
│   ├── App.tsx                   # Main React Root Component
│   ├── App.css                   # Global Application Layout Styles
│   ├── index.css                 # Tailwind CSS v4 Theme, Fonts & Tokens
│   └── main.tsx                  # Vite DOM Mount Entry Point
│
├── public/                       # Static Public Assets (Favicons, Meta Images)
├── components.json               # shadcn/ui & Skiper UI Registry Configuration
├── vite.config.ts                # Vite 8 Config (React plugins, path aliases)
├── package.json                  # Dependencies, scripts, and engine specifications
├── tsconfig.json                 # TypeScript project configuration references
├── tsconfig.app.json             # App TypeScript compiler settings
├── tsconfig.node.json            # Vite Node configuration
├── vercel.json                   # Vercel SPA routing & caching rules
└── .oxlintrc.json                # Oxlint high-speed linting rules
```

---

## 🛠️ Technology Stack Breakdown

| Layer | Technology | Version | Purpose |
| :--- | :--- | :---: | :--- |
| **Core Framework** | **React** | `19.2.8` | Component lifecycle, modern hooks, and state management |
| **Language** | **TypeScript** | `~6.0.2` | Strict end-to-end type safety |
| **Build Tooling** | **Vite** | `^8.3.0` | Next-generation ES module bundler and fast HMR dev server |
| **Styling** | **Tailwind CSS v4** | `^4.3.3` | Modern CSS-first design tokens via `@tailwindcss/vite` |
| **Component System**| **shadcn/ui** | New York | Accessible, customizable primitive base |
| **Interactive UI** | **Skiper UI** | `@skiper-ui` | Specialized accordion galleries, interactive terminal, and cards |
| **Animations** | **Framer Motion** | `^14.0.0` | Declarative transitions, stagger effects, and layout animations |
| **Smooth Scrolling**| **Lenis** | `^1.3.26` | High-fidelity scroll physics |
| **Icons** | **Lucide React** | `^1.51.0` | Consistent, lightweight SVG icon system |
| **Hooks Utility** | **usehooks-ts** | `^3.1.1` | Production-ready custom React hooks (resize, scroll, state) |
| **Linter** | **Oxlint** | `^1.81.0` | Ultra-fast Rust-based linter |
| **Hosting** | **Vercel** | — | Edge deployment with automatic CI/CD sync |

---

## 🚀 Developer Quickstart

### 1. Install Dependencies
```bash
cd website
npm install
```

### 2. Run Local Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Production Build
```bash
npm run build
```
Typechecks with `tsc -b` and compiles the optimized production bundle into `dist/`.

### 4. Run Linter
```bash
npm run lint
```
Executes `oxlint` for lightning-fast linting across all TypeScript/TSX files.

### 5. Local Production Preview
```bash
npm run preview
```
Previews the compiled production bundle locally before deploying.

---

## 🛡️ Coding & Workflow Guidelines

1. **Uniform Component Hierarchy**: All components live strictly inside `src/components/` and `src/components/v1/`. Never create root-level component folders.
2. **Path Aliasing**: Always import via configured `@/` aliases (`@/components`, `@/lib/utils`, `@/hooks`).
3. **Responsive Design**: All sections are fully responsive across mobile, tablet, and widescreen layouts.
