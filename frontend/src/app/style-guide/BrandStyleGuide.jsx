"use client";
import { useState, useEffect, useRef } from "react";

//globals.css choice explainations
const TOKENS = {
  colors: {
    brand: [
      { name: "Void", hex: "#0A0A0A", rgb: "10, 10, 10", hsl: "0°, 0%, 4%", usage: "Deepest background, modal overlays", token: "--color-void", textColor: "#F5F5F5" },
      { name: "Abyss", hex: "#0D0D0D", rgb: "13, 13, 13", hsl: "0°, 0%, 5%", usage: "Sidebar background, primary canvas", token: "--color-abyss", textColor: "#F5F5F5" },
      { name: "Depth", hex: "#141414", rgb: "20, 20, 20", hsl: "0°, 0%, 8%", usage: "Card backgrounds on dark surfaces", token: "--color-depth", textColor: "#F5F5F5" },
      { name: "Slate", hex: "#1E1E1E", rgb: "30, 30, 30", hsl: "0°, 0%, 12%", usage: "Hover states, secondary containers", token: "--color-slate", textColor: "#F5F5F5" },
      { name: "Gunmetal", hex: "#8A8A8A", rgb: "138, 138, 138", hsl: "0°, 0%, 54%", usage: "Disabled states, borders, dividers", token: "--color-gunmetal", textColor: "#0A0A0A" },
      { name: "Ash", hex: "#A3A3A3", rgb: "163, 163, 163", hsl: "0°, 0%, 64%", usage: "Muted body text, secondary labels", token: "--color-ash", textColor: "#0A0A0A" },
      { name: "Frost", hex: "#F5F5F5", rgb: "245, 245, 245", hsl: "0°, 0%, 96%", usage: "Primary text on dark, high contrast", token: "--color-frost", textColor: "#0A0A0A" },
    ],
    accent: [
      { name: "Emerald", hex: "#10B981", rgb: "16, 185, 129", hsl: "160°, 84%, 39%", usage: "Primary action, brand accent, links, focus rings", token: "--color-green", textColor: "#0A0A0A" },
      { name: "Pulse", hex: "#2D7EFF", rgb: "45, 126, 255", hsl: "218°, 100%, 59%", usage: "Informational alerts, data visualisation secondary", token: "--color-pulse", textColor: "#FFFFFF" },
      { name: "Ice", hex: "#6AB0FF", rgb: "106, 176, 255", hsl: "213°, 100%, 71%", usage: "Hover state of informational, tag highlights", token: "--color-ice", textColor: "#0A0A0A" },
    ],
    semantic: [
      { name: "Threat", hex: "#EF4444", rgb: "239, 68, 68", hsl: "0°, 83%, 60%", usage: "Destructive actions, error states, critical alerts", token: "--color-threat", textColor: "#FFFFFF" },
      { name: "Caution", hex: "#F59E0B", rgb: "245, 158, 11", hsl: "38°, 92%, 50%", usage: "Warnings, medium-risk detections, expiry notices", token: "--color-caution", textColor: "#0A0A0A" },
      { name: "Safe", hex: "#10B981", rgb: "16, 185, 129", hsl: "160°, 84%, 39%", usage: "Success states, confirmed detections, system healthy", token: "--color-safe", textColor: "#0A0A0A" },
      { name: "Info", hex: "#2D7EFF", rgb: "45, 126, 255", hsl: "218°, 100%, 59%", usage: "Informational banners, non-urgent system messages", token: "--color-info", textColor: "#FFFFFF" },
    ],
  },
  contrast: [
    { pair: "Frost on Abyss", fg: "#F5F5F5", bg: "#0D0D0D", ratio: "18.1:1", level: "AAA", usage: "Primary body text" },
    { pair: "Emerald on Abyss", fg: "#10B981", bg: "#0D0D0D", ratio: "7.2:1", level: "AAA", usage: "Brand accent text" },
    { pair: "Ash on Abyss", fg: "#A3A3A3", bg: "#0D0D0D", ratio: "8.9:1", level: "AAA", usage: "Secondary text" },
    { pair: "Frost on Slate", fg: "#F5F5F5", bg: "#1E1E1E", ratio: "14.5:1", level: "AAA", usage: "Card content text" },
    { pair: "Abyss on Emerald", fg: "#0A0A0A", bg: "#10B981", ratio: "7.2:1", level: "AAA", usage: "Primary button label" },
    { pair: "Frost on Depth", fg: "#F5F5F5", bg: "#141414", ratio: "16.8:1", level: "AAA", usage: "Card headings" },
    { pair: "Threat on Abyss", fg: "#EF4444", bg: "#0D0D0D", ratio: "4.7:1", level: "AA", usage: "Error state text" },
    { pair: "Caution on Abyss", fg: "#F59E0B", bg: "#0D0D0D", ratio: "5.8:1", level: "AA", usage: "Warning text" },
  ],
  type: [
    { name: "Display", size: "3rem", lineHeight: "3.5rem", weight: "700", token: "--text-display", sample: "WatchDog", usage: "Hero headlines, splash screens" },
    { name: "H1", size: "2rem", lineHeight: "2.5rem", weight: "700", token: "--text-h1", sample: "Neighbourhood Security", usage: "Page-level headings" },
    { name: "H2", size: "1.5rem", lineHeight: "2rem", weight: "600", token: "--text-h2", sample: "Camera Feeds", usage: "Section headings" },
    { name: "H3", size: "1.25rem", lineHeight: "1.75rem", weight: "600", token: "--text-h3", sample: "Alert summary", usage: "Card headings, subsections" },
    { name: "Body LG", size: "1.125rem", lineHeight: "1.75rem", weight: "400", token: "--text-body-lg", sample: "Monitored zones detected 3 events.", usage: "Lead paragraph text" },
    { name: "Body", size: "1rem", lineHeight: "1.5rem", weight: "400", token: "--text-body", sample: "Camera is active and streaming.", usage: "Standard interface text" },
    { name: "Small", size: "0.875rem", lineHeight: "1.25rem", weight: "400", token: "--text-sm", sample: "Last updated 2 min ago", usage: "Labels, helper text" },
    { name: "Caption", size: "0.75rem", lineHeight: "1rem", weight: "400", token: "--text-caption", sample: "Zone B — Perimeter", usage: "Timestamps, metadata" },
    { name: "Code", size: "0.875rem", lineHeight: "1.25rem", weight: "400", token: "--text-code", sample: "camera.stream.start()", usage: "Code snippets, IDs", mono: true },
  ],
  spacing: [
    { token: "--space-1", value: "4px", usage: "Icon gap, micro nudge" },
    { token: "--space-2", value: "8px", usage: "Inline element gap" },
    { token: "--space-3", value: "12px", usage: "Input padding, compact rows" },
    { token: "--space-4", value: "16px", usage: "Card padding, section gap" },
    { token: "--space-5", value: "24px", usage: "Component margin, between cards" },
    { token: "--space-6", value: "32px", usage: "Section separator" },
    { token: "--space-8", value: "48px", usage: "Page section spacing" },
    { token: "--space-10", value: "64px", usage: "Hero vertical padding" },
    { token: "--space-12", value: "96px", usage: "Full-bleed section height" },
  ],
  radius: [
    { token: "--radius-sm", value: "4px", usage: "Badges, chips, small tags" },
    { token: "--radius-md", value: "8px", usage: "Inputs, buttons, dropdowns" },
    { token: "--radius-lg", value: "12px", usage: "Cards, modals, panels" },
    { token: "--radius-xl", value: "16px", usage: "Sheets, overlays, sidebars" },
    { token: "--radius-full", value: "9999px", usage: "Pills, avatar circles, toggles" },
  ],
  motion: [
    { token: "--motion-instant", value: "0ms", usage: "State changes requiring no animation" },
    { token: "--motion-fast", value: "100ms ease-out", usage: "Hover feedback, button press" },
    { token: "--motion-normal", value: "200ms ease-in-out", usage: "Panel open/close, accordion" },
    { token: "--motion-slow", value: "350ms ease-in-out", usage: "Modal entrance, page transitions" },
    { token: "--motion-alert-pulse", value: "1200ms ease-in-out infinite", usage: "Active threat indicator pulse" },
  ],
  shadows: [
    { token: "--shadow-sm", value: "0 1px 3px rgba(0,0,0,0.3)", usage: "Subtle card lift" },
    { token: "--shadow-md", value: "0 4px 12px rgba(0,0,0,0.4)", usage: "Dropdown menus, tooltips" },
    { token: "--shadow-lg", value: "0 8px 24px rgba(0,0,0,0.5)", usage: "Modals, sheets" },
    { token: "--shadow-alert", value: "0 0 0 3px rgba(239,68,68,0.30)", usage: "Error focus ring" },
  ],
  breakpoints: [
    { name: "Mobile", value: "< 640px", cols: "1", notes: "Single column, stacked nav" },
    { name: "Tablet", value: "640px – 1023px", cols: "2", notes: "Two columns, condensed sidebar" },
    { name: "Desktop", value: "1024px – 1279px", cols: "3", notes: "Full layout with sidebar" },
    { name: "Wide", value: "≥ 1280px", cols: "4", notes: "Extended grid, multi-feed view" },
  ],
};

//header functions and transition functions
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgb(${r}, ${g}, ${b})`;
}

function useIntersection(ref) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.1 });
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return visible;
}

function FadeIn({ children, delay = 0, className = "" }) {
  const ref = useRef(null);
  const visible = useIntersection(ref);
  return (
    <div ref={ref} className={className} style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)", transition: `opacity 0.5s ease ${delay}ms, transform 0.5s ease ${delay}ms` }}>
      {children}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px" }}>
      <div style={{ width: "3px", height: "24px", background: "#10B981", borderRadius: "2px", flexShrink: 0 }} />
      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#10B981", fontWeight: 500 }}>{children}</span>
    </div>
  );
}

function SectionHeading({ children }) {
  return <h2 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#F5F5F5", marginBottom: "8px", letterSpacing: "-0.02em" }}>{children}</h2>;
}

function SectionSubtitle({ children }) {
  return <p style={{ fontSize: "0.9375rem", color: "#8A8A8A", lineHeight: "1.6", marginBottom: "40px", maxWidth: "560px" }}>{children}</p>;
}

function Card({ children, style = {} }) {
  return (
    <div style={{ background: "#141414", border: "1px solid rgba(138,138,138,0.12)", borderRadius: "12px", padding: "24px", ...style }}>
      {children}
    </div>
  );
}

function Token({ children }) {
  return (
    <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", background: "#1E1E1E", color: "#10B981", padding: "2px 6px", borderRadius: "4px", whiteSpace: "nowrap" }}>
      {children}
    </code>
  );
}

function HeroSection() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 2000);
    return () => clearInterval(id);
  }, []);

  const words = ["Security.", "Clarity.", "Trust.", "Identity."];
  const current = words[tick % words.length];

  return (
    <section style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", padding: "80px 64px", background: "#0A0A0A", position: "relative", overflow: "hidden" }}>
      {/* Grid overlay */}
      <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(rgba(16,185,129,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.04) 1px, transparent 1px)", backgroundSize: "48px 48px", pointerEvents: "none" }} />
      {/* Glow */}
      <div style={{ position: "absolute", top: "30%", left: "50%", transform: "translate(-50%,-50%)", width: "600px", height: "600px", background: "radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ position: "relative", zIndex: 1, maxWidth: "800px" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "#1E1E1E", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "9999px", padding: "6px 14px", marginBottom: "32px" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10B981", animation: "pulse 1.2s ease-in-out infinite" }} />
          {/* <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#10B981", letterSpacing: "0.1em" }}>Demo 2 · Brand Style Guide</span> */}
        </div>

        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ fontSize: "clamp(3rem, 7vw, 5.5rem)", fontWeight: 700, color: "#F5F5F5", lineHeight: 1.05, letterSpacing: "-0.04em", margin: 0 }}>
            Neighbourhood<br />WatchDog
          </h1>
          <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginTop: "8px" }}>
            <span style={{ fontSize: "clamp(1.5rem, 3vw, 2.5rem)", fontWeight: 300, color: "#8A8A8A", letterSpacing: "-0.02em" }}>Designed for</span>
            <span key={current} style={{ fontSize: "clamp(1.5rem, 3vw, 2.5rem)", fontWeight: 700, color: "#10B981", letterSpacing: "-0.02em", animation: "fadeWord 0.4s ease" }}>{current}</span>
          </div>
        </div>

        <p style={{ fontSize: "1.0625rem", color: "#A3A3A3", lineHeight: 1.7, maxWidth: "520px", marginBottom: "48px" }}>
          An AI-assisted CCTV security platform built for EPI-USE Africa. This guide documents the complete visual language, design tokens, and component system powering the production interface.
        </p>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {["Colours", "Typography", "Tokens", "Components", "Accessibility"].map((s, i) => (
            <a key={s} href={`#${s.toLowerCase()}`} style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.2)", color: "#A3A3A3", fontSize: "13px", textDecoration: "none", transition: "all 0.15s", background: "transparent" }}
              onMouseEnter={e => { e.target.style.borderColor = "rgba(16,185,129,0.4)"; e.target.style.color = "#F5F5F5"; }}
              onMouseLeave={e => { e.target.style.borderColor = "rgba(138,138,138,0.2)"; e.target.style.color = "#A3A3A3"; }}>
              {s}
            </a>
          ))}
        </div>
      </div>

      {/* Version badge */}
      <div style={{ position: "absolute", bottom: "40px", right: "64px", fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#3D3D3D" }}>
        Zero Day Proking Solutions · v2.0
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.4)} }
        @keyframes fadeWord { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </section>
  );
}

function ColoursSection() {
  const [copied, setCopied] = useState(null);
  const copy = (hex, id) => { navigator.clipboard?.writeText(hex); setCopied(id); setTimeout(() => setCopied(null), 1500); };

  return (
    <section id="colours" style={{ padding: "96px 64px", background: "#0D0D0D" }}>
      <FadeIn>
        {/* <SectionLabel>01 - Colour</SectionLabel> */}
        <SectionHeading>Colour palette</SectionHeading>
        <SectionSubtitle>A dark-first monochromatic system anchored by emerald green. Every colour serves a defined role - decorative use is not permitted.</SectionSubtitle>
      </FadeIn>

      {[
        { title: "Brand neutrals", desc: "The greyscale foundation. Builds depth and hierarchy across surfaces.", data: TOKENS.colors.brand },
        { title: "Accent colours", desc: "Emerald is the primary brand colour. Pulse and Ice are for informational contexts only.", data: TOKENS.colors.accent },
        { title: "Semantic colours", desc: "Reserved for system states. Never use these for decorative purposes.", data: TOKENS.colors.semantic },
      ].map(({ title, desc, data }) => (
        <FadeIn key={title} delay={100}>
          <div style={{ marginBottom: "56px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#F5F5F5", marginBottom: "4px" }}>{title}</h3>
            <p style={{ fontSize: "13px", color: "#8A8A8A", marginBottom: "20px" }}>{desc}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "12px" }}>
              {data.map((c, i) => (
                <div key={c.name} onClick={() => copy(c.hex, `${title}-${i}`)}
                  style={{ borderRadius: "10px", overflow: "hidden", border: "1px solid rgba(138,138,138,0.1)", cursor: "pointer", transition: "transform 0.15s, box-shadow 0.15s" }}
                  onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.4)"; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = ""; }}>
                  <div style={{ height: "72px", background: c.hex, display: "flex", alignItems: "flex-end", padding: "8px 10px" }}>
                    {copied === `${title}-${i}` && <span style={{ fontSize: "10px", color: c.textColor, fontFamily: "'JetBrains Mono', monospace", opacity: 0.8 }}>Copied!</span>}
                  </div>
                  <div style={{ background: "#1E1E1E", padding: "10px 12px" }}>
                    <p style={{ fontSize: "13px", fontWeight: 600, color: "#F5F5F5", margin: "0 0 2px" }}>{c.name}</p>
                    <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#10B981", margin: "0 0 6px" }}>{c.hex}</p>
                    <p style={{ fontSize: "11px", color: "#8A8A8A", margin: "0 0 2px" }}>rgb({c.rgb})</p>
                    <p style={{ fontSize: "11px", color: "#8A8A8A", margin: "0 0 8px" }}>{c.hsl}</p>
                    <p style={{ fontSize: "11px", color: "#6B6B6B", margin: 0, lineHeight: 1.4 }}>{c.usage}</p>
                    <div style={{ marginTop: "8px" }}><Token>{c.token}</Token></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      ))}

      <FadeIn delay={150}>
        <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#F5F5F5", marginBottom: "4px" }}>WCAG 2.2 contrast ratios</h3>
        <p style={{ fontSize: "13px", color: "#8A8A8A", marginBottom: "20px" }}>All foreground/background pairs used in the live UI. AA (4.5:1) is the minimum; AAA (7:1) is achieved for all body text pairings.</p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(138,138,138,0.15)" }}>
                {["Pair", "Preview", "Ratio", "Level", "Usage"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "#8A8A8A", fontWeight: 500, fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TOKENS.contrast.map((row, i) => (
                <tr key={i} style={{ borderBottom: "1px solid rgba(138,138,138,0.08)", transition: "background 0.1s" }}
                  onMouseEnter={e => e.currentTarget.style.background = "#1A1A1A"}
                  onMouseLeave={e => e.currentTarget.style.background = ""}>
                  <td style={{ padding: "12px 14px", color: "#F5F5F5", fontWeight: 500 }}>{row.pair}</td>
                  <td style={{ padding: "12px 14px" }}>
                    <div style={{ background: row.bg, borderRadius: "6px", padding: "4px 10px", display: "inline-block" }}>
                      <span style={{ color: row.fg, fontSize: "12px", fontWeight: 600 }}>Aa</span>
                    </div>
                  </td>
                  <td style={{ padding: "12px 14px", fontFamily: "'JetBrains Mono', monospace", color: "#10B981" }}>{row.ratio}</td>
                  <td style={{ padding: "12px 14px" }}>
                    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "4px", fontSize: "11px", fontWeight: 600, fontFamily: "'JetBrains Mono', monospace", background: row.level === "AAA" ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)", color: row.level === "AAA" ? "#10B981" : "#F59E0B" }}>{row.level}</span>
                  </td>
                  <td style={{ padding: "12px 14px", color: "#8A8A8A" }}>{row.usage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </FadeIn>
    </section>
  );
}

function TypographySection() {
  return (
    <section id="typography" style={{ padding: "96px 64px", background: "#0A0A0A" }}>
      <FadeIn>
        {/* <SectionLabel>02 - Typography</SectionLabel> */}
        <SectionHeading>Type system</SectionHeading>
        <SectionSubtitle>Inter for interface text - geometric, neutral, legible at all sizes. JetBrains Mono for code, IDs, tokens, and technical strings. Both sourced from Google Fonts under the SIL Open Font Licence.</SectionSubtitle>
      </FadeIn>

      <FadeIn delay={100}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "48px" }}>
          {[
            { name: "Inter", role: "UI / Interface", weights: "300, 400, 500, 600, 700", fallback: "system-ui, sans-serif", source: "Google Fonts · SIL OFL", token: "--font-sans", sample: "ABCDEFGHIJKLM\nnopqrstuvwxyz\n0123456789!@#" },
            { name: "JetBrains Mono", role: "Code / Technical", weights: "400, 500, 700", fallback: "Consolas, monospace", source: "Google Fonts · SIL OFL", token: "--font-mono", sample: "const cam = new\nStream({ zone: 'B' })\nreturn cam.init()" },
          ].map(f => (
            <Card key={f.name}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div>
                  <p style={{ fontSize: "11px", color: "#8A8A8A", margin: "0 0 4px", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>{f.role}</p>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F5F5F5", margin: "0 0 4px", fontFamily: f.name.includes("Mono") ? "'JetBrains Mono', monospace" : "Inter, sans-serif" }}>{f.name}</h3>
                </div>
                <Token>{f.token}</Token>
              </div>
              <pre style={{ fontFamily: f.name.includes("Mono") ? "'JetBrains Mono', monospace" : "Inter, sans-serif", fontSize: "28px", fontWeight: 400, color: "#F5F5F5", background: "#1E1E1E", borderRadius: "8px", padding: "16px", margin: "0 0 16px", lineHeight: 1.3, overflow: "hidden" }}>{f.sample}</pre>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px", color: "#8A8A8A" }}>
                <span>Weights: {f.weights}</span>
                <span>Source: {f.source}</span>
                <span style={{ gridColumn: "span 2" }}>Fallback: <code style={{ color: "#A3A3A3" }}>{f.fallback}</code></span>
              </div>
            </Card>
          ))}
        </div>
      </FadeIn>

      <FadeIn delay={150}>
        <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#F5F5F5", marginBottom: "20px" }}>Type scale</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          {TOKENS.type.map((t, i) => (
            <div key={t.name} style={{ display: "grid", gridTemplateColumns: "120px 1fr 200px", alignItems: "center", gap: "16px", padding: "16px", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.08)", background: "#141414", transition: "background 0.1s" }}
              onMouseEnter={e => e.currentTarget.style.background = "#1A1A1A"}
              onMouseLeave={e => e.currentTarget.style.background = "#141414"}>
              <div>
                <p style={{ fontSize: "11px", color: "#8A8A8A", margin: "0 0 2px" }}>{t.name}</p>
                <Token>{t.token}</Token>
              </div>
              <div style={{ fontFamily: t.mono ? "'JetBrains Mono', monospace" : "Inter, sans-serif", fontSize: t.size, fontWeight: t.weight, color: "#F5F5F5", lineHeight: t.lineHeight, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>{t.sample}</div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#10B981", margin: "0 0 2px" }}>{t.size} / {t.lineHeight}</p>
                <p style={{ fontSize: "11px", color: "#6B6B6B", margin: 0 }}>w{t.weight} · {t.usage}</p>
              </div>
            </div>
          ))}
        </div>
      </FadeIn>
    </section>
  );
}

function LogoSection() {
  const logoVariants = [
    { label: "Full", bg: "#0D0D0D", border: "1px solid rgba(138,138,138,0.12)" },
    { label: "Inverse", bg: "#F5F5F5", border: "none" },
    { label: "Monochrome", bg: "#1E1E1E", border: "1px solid rgba(138,138,138,0.12)", mono: true },
  ];

  function LogoMark({ color = "#10B981", textColor = "#F5F5F5", size = 1 }) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: `${12 * size}px` }}>
        <svg width={`${40 * size}`} height={`${40 * size}`} viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="10" fill={color} />
          <path d="M20 8 L32 14 L32 22 C32 28 26 34 20 36 C14 34 8 28 8 22 L8 14 Z" fill="none" stroke={color === "#F5F5F5" ? "#0A0A0A" : "#0A0A0A"} strokeWidth="2.5" />
          <circle cx="20" cy="22" r="4" fill={color === "#F5F5F5" ? "#0A0A0A" : "#0A0A0A"} />
          <path d="M20 18 L20 10" stroke={color === "#F5F5F5" ? "#0A0A0A" : "#0A0A0A"} strokeWidth="2" strokeLinecap="round" />
        </svg>
        <div>
          <p style={{ fontSize: `${14 * size}px`, fontWeight: 700, color: textColor, margin: 0, letterSpacing: "-0.02em", lineHeight: 1.1 }}>WatchDog</p>
          <p style={{ fontSize: `${10 * size}px`, color: color === "#F5F5F5" ? "#555" : "#A3A3A3", margin: 0, letterSpacing: "0.12em", textTransform: "uppercase", fontFamily: "'JetBrains Mono', monospace" }}>Neighbourhood Security</p>
        </div>
      </div>
    );
  }

  return (
    <section id="logo" style={{ padding: "96px 64px", background: "#0D0D0D" }}>
      <FadeIn>
        {/* <SectionLabel>03 - Logo & Iconography</SectionLabel> */}
        <SectionHeading>Logo system</SectionHeading>
        <SectionSubtitle>The WatchDog mark is a shield with an embedded camera - surveillance, protection, and AI-driven intelligence in a single glyph. Do not alter proportions, colours, or orientation.</SectionSubtitle>
      </FadeIn>

      <FadeIn delay={100}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "40px" }}>
          <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "140px", background: "#0D0D0D" }}>
            <div style={{ marginBottom: "16px" }}><svg width="40" height="40" viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="10" fill="#10B981" /><path d="M20 8 L32 14 L32 22 C32 28 26 34 20 36 C14 34 8 28 8 22 L8 14 Z" fill="none" stroke="#0A0A0A" strokeWidth="2.5" /><circle cx="20" cy="22" r="4" fill="#0A0A0A" /><path d="M20 18 L20 10" stroke="#0A0A0A" strokeWidth="2" strokeLinecap="round" /></svg></div>
            <div style={{ textAlign: "center" }}><p style={{ fontSize: "14px", fontWeight: 700, color: "#F5F5F5", margin: "0 0 2px" }}>WatchDog</p><p style={{ fontSize: "10px", color: "#A3A3A3", margin: 0, letterSpacing: "0.1em", textTransform: "uppercase", fontFamily: "monospace" }}>Neighbourhood Security</p></div>
            <p style={{ fontSize: "11px", color: "#6B6B6B", marginTop: "12px" }}>Full - dark bg</p>
          </Card>
          <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "140px", background: "#F5F5F5" }}>
            <div style={{ marginBottom: "16px" }}><svg width="40" height="40" viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="10" fill="#0A0A0A" /><path d="M20 8 L32 14 L32 22 C32 28 26 34 20 36 C14 34 8 28 8 22 L8 14 Z" fill="none" stroke="#F5F5F5" strokeWidth="2.5" /><circle cx="20" cy="22" r="4" fill="#F5F5F5" /><path d="M20 18 L20 10" stroke="#F5F5F5" strokeWidth="2" strokeLinecap="round" /></svg></div>
            <div style={{ textAlign: "center" }}><p style={{ fontSize: "14px", fontWeight: 700, color: "#0A0A0A", margin: "0 0 2px" }}>WatchDog</p><p style={{ fontSize: "10px", color: "#555", margin: 0, letterSpacing: "0.1em", textTransform: "uppercase", fontFamily: "monospace" }}>Neighbourhood Security</p></div>
            <p style={{ fontSize: "11px", color: "#888", marginTop: "12px" }}>Inverse - light bg</p>
          </Card>
          <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "140px", background: "#1E1E1E" }}>
            <div style={{ marginBottom: "16px" }}><svg width="40" height="40" viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="10" fill="#8A8A8A" /><path d="M20 8 L32 14 L32 22 C32 28 26 34 20 36 C14 34 8 28 8 22 L8 14 Z" fill="none" stroke="#1E1E1E" strokeWidth="2.5" /><circle cx="20" cy="22" r="4" fill="#1E1E1E" /><path d="M20 18 L20 10" stroke="#1E1E1E" strokeWidth="2" strokeLinecap="round" /></svg></div>
            <div style={{ textAlign: "center" }}><p style={{ fontSize: "14px", fontWeight: 700, color: "#8A8A8A", margin: "0 0 2px" }}>WatchDog</p><p style={{ fontSize: "10px", color: "#6B6B6B", margin: 0, letterSpacing: "0.1em", textTransform: "uppercase", fontFamily: "monospace" }}>Neighbourhood Security</p></div>
            <p style={{ fontSize: "11px", color: "#6B6B6B", marginTop: "12px" }}>Monochrome</p>
          </Card>
        </div>
      </FadeIn>

      <FadeIn delay={150}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "40px" }}>
          <Card>
            <h3 style={{ fontSize: "13px", fontWeight: 600, color: "#F5F5F5", marginBottom: "16px" }}>Clear-space & minimum size</h3>
            <div style={{ background: "#1E1E1E", borderRadius: "8px", padding: "24px", display: "flex", alignItems: "center", justifyContent: "center", gap: "16px", marginBottom: "12px" }}>
              <div style={{ position: "relative", border: "1px dashed rgba(16,185,129,0.3)", padding: "12px" }}>
                <svg width="32" height="32" viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="10" fill="#10B981" /><path d="M20 8 L32 14 L32 22 C32 28 26 34 20 36 C14 34 8 28 8 22 L8 14 Z" fill="none" stroke="#0A0A0A" strokeWidth="2.5" /><circle cx="20" cy="22" r="4" fill="#0A0A0A" /></svg>
                <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, border: "1px dashed rgba(16,185,129,0.4)", borderRadius: "2px", pointerEvents: "none" }} />
              </div>
              <div style={{ fontSize: "12px", color: "#8A8A8A", lineHeight: 1.6 }}>
                <p style={{ margin: "0 0 4px" }}>Clear space = ½ shield height</p>
                <p style={{ margin: 0 }}>Min render: 24×24px (icon), 120px (full)</p>
              </div>
            </div>
          </Card>
          <Card>
            <h3 style={{ fontSize: "13px", fontWeight: 600, color: "#EF4444", marginBottom: "16px" }}>Forbidden treatments</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {["Do not stretch or skew the mark", "Do not recolour the shield (emerald or monochrome only)", "Do not add drop shadows or glow effects", "Do not place on a busy photographic background", "Do not rotate or flip the mark", "Do not use outline-only version of filled icon"].map(r => (
                <div key={r} style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                  <span style={{ color: "#EF4444", fontSize: "12px", flexShrink: 0, marginTop: "1px" }}>✕</span>
                  <span style={{ fontSize: "12px", color: "#8A8A8A", lineHeight: 1.5 }}>{r}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </FadeIn>

      <FadeIn delay={200}>
        <Card>
          <h3 style={{ fontSize: "13px", fontWeight: 600, color: "#F5F5F5", marginBottom: "4px" }}>Icon library - Lucide React</h3>
          <p style={{ fontSize: "12px", color: "#8A8A8A", marginBottom: "16px" }}>All UI icons are sourced from Lucide React. Stroke weight: 1.5px at 16–20px, 2px at 24px+. Never fill icons unless explicitly a filled-state indicator.</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {[].map(icon => (
              <div key={icon.name} style={{ display: "flex", alignItems: "center", gap: "6px", background: "#1E1E1E", borderRadius: "6px", padding: "6px 10px" }}>
                <span style={{ fontSize: "14px" }}>{icon.unicode}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#A3A3A3" }}>{icon.name}</span>
              </div>
            ))}
          </div>
        </Card>
      </FadeIn>
    </section>
  );
}

function TokensSection() {
  const [activeTab, setActiveTab] = useState("spacing");
  const tabs = ["spacing", "radius", "motion", "shadows", "breakpoints"];

  const tabData = {
    spacing: TOKENS.spacing,
    radius: TOKENS.radius,
    motion: TOKENS.motion,
    shadows: TOKENS.shadows,
    breakpoints: TOKENS.breakpoints,
  };

  return (
    <section id="tokens" style={{ padding: "96px 64px", background: "#0A0A0A" }}>
      <FadeIn>
        {/* <SectionLabel>04 - Design Tokens</SectionLabel> */}
        <SectionHeading>Token system</SectionHeading>
        <SectionSubtitle>All values are defined as CSS custom properties in globals.css. Any drift between this guide and the codebase is treated as a bug.</SectionSubtitle>
      </FadeIn>

      <FadeIn delay={100}>
        <div style={{ display: "flex", gap: "4px", marginBottom: "24px", background: "#141414", padding: "4px", borderRadius: "10px", display: "inline-flex", flexWrap: "wrap" }}>
          {tabs.map(t => (
            <button key={t} onClick={() => setActiveTab(t)}
              style={{ padding: "7px 16px", borderRadius: "7px", border: "none", cursor: "pointer", fontSize: "13px", fontWeight: 500, transition: "all 0.15s", background: activeTab === t ? "#10B981" : "transparent", color: activeTab === t ? "#0A0A0A" : "#8A8A8A", textTransform: "capitalize" }}>
              {t}
            </button>
          ))}
        </div>

        {activeTab === "spacing" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {TOKENS.spacing.map(s => (
              <div key={s.token} style={{ display: "grid", gridTemplateColumns: "200px 80px 1fr 200px", alignItems: "center", gap: "16px", padding: "12px 16px", background: "#141414", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.08)" }}>
                <Token>{s.token}</Token>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "#F5F5F5" }}>{s.value}</span>
                <div style={{ background: "#10B981", height: "8px", borderRadius: "4px", opacity: 0.8, width: s.value }} />
                <span style={{ fontSize: "12px", color: "#8A8A8A" }}>{s.usage}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === "radius" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {TOKENS.radius.map(r => (
              <div key={r.token} style={{ display: "grid", gridTemplateColumns: "200px 80px 80px 1fr", alignItems: "center", gap: "16px", padding: "12px 16px", background: "#141414", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.08)" }}>
                <Token>{r.token}</Token>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "#F5F5F5" }}>{r.value}</span>
                <div style={{ width: "40px", height: "40px", border: "2px solid #10B981", borderRadius: r.value, background: "rgba(16,185,129,0.1)" }} />
                <span style={{ fontSize: "12px", color: "#8A8A8A" }}>{r.usage}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === "motion" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {TOKENS.motion.map(m => (
              <div key={m.token} style={{ display: "grid", gridTemplateColumns: "240px 1fr 220px", alignItems: "center", gap: "16px", padding: "12px 16px", background: "#141414", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.08)" }}>
                <Token>{m.token}</Token>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "#F5F5F5" }}>{m.value}</span>
                <span style={{ fontSize: "12px", color: "#8A8A8A" }}>{m.usage}</span>
              </div>
            ))}
            <Card style={{ marginTop: "16px" }}>
              <p style={{ fontSize: "12px", color: "#8A8A8A", marginBottom: "12px" }}>All transitions respect <Token>prefers-reduced-motion</Token> - durations collapse to 0ms when the user has requested reduced motion in their OS settings.</p>
              <code style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "#10B981", background: "#1E1E1E", padding: "12px", borderRadius: "6px", lineHeight: 1.7 }}>
                {"@media (prefers-reduced-motion: reduce) {\n  *, *::before, *::after {\n    animation-duration: 0.01ms !important;\n    transition-duration: 0.01ms !important;\n  }\n}"}
              </code>
            </Card>
          </div>
        )}

        {activeTab === "shadows" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px" }}>
            {TOKENS.shadows.map(s => (
              <div key={s.token} style={{ background: "#141414", borderRadius: "10px", padding: "20px", border: "1px solid rgba(138,138,138,0.08)" }}>
                <div style={{ width: "100%", height: "60px", background: "#1E1E1E", borderRadius: "8px", boxShadow: s.value, marginBottom: "16px" }} />
                <Token>{s.token}</Token>
                <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#8A8A8A", marginTop: "6px", marginBottom: "4px", wordBreak: "break-all" }}>{s.value}</p>
                <p style={{ fontSize: "12px", color: "#6B6B6B" }}>{s.usage}</p>
              </div>
            ))}
          </div>
        )}

        {activeTab === "breakpoints" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {TOKENS.breakpoints.map(b => (
              <div key={b.name} style={{ display: "grid", gridTemplateColumns: "100px 200px 60px 1fr", alignItems: "center", gap: "16px", padding: "12px 16px", background: "#141414", borderRadius: "8px", border: "1px solid rgba(138,138,138,0.08)" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#F5F5F5" }}>{b.name}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", color: "#10B981" }}>{b.value}</span>
                <span style={{ fontSize: "12px", color: "#F5F5F5", fontWeight: 600 }}>{b.cols} col{b.cols > 1 ? "s" : ""}</span>
                <span style={{ fontSize: "12px", color: "#8A8A8A" }}>{b.notes}</span>
              </div>
            ))}
          </div>
        )}
      </FadeIn>
    </section>
  );
}


export default function StyleGuide() {
  return (
    <div style={{ fontFamily: "Inter, system-ui, sans-serif", background: "#0A0A0A", minHeight: "100vh", color: "#F5F5F5" }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
      {/* <Nav /> */}
      <HeroSection />
      <ColoursSection />
      <TypographySection />
      <LogoSection />
      <TokensSection />
    </div>
  );
}