// ============================================================
// SHELL PRIMITIVES (Phase 1, greenfield) — NOT yet consumed by any shipped surface.
// Two net-new pieces the Three-Zone migration is built on:
//   • RightStack — the inspect-panel STACK. depth 1 = a single card; an in-panel drill
//     PUSHES a card on top with a back link; pop UNCOVERS the one beneath WITHOUT a
//     re-fetch (lower layers stay mounted, hidden, so their state + scroll survive).
//   • Shell — the four-slot frame (top nav lives above it) WITH a real desktop→mobile
//     collapse: desktop = rail | center | inspect (the .z* frame); mobile = center inline
//     + a bottom toolbar that opens the rail / inspect as swipe-dismiss sheets.
// Decisions locked in the handoff (rev 2): restore-on-pop is UNIVERSAL for new surfaces;
// the parent OWNS the stack array (via useRightStack) so center peer-select can reset() it;
// children DRILL by calling useRightStackCtl().push(). Keys are push-unique (a minted id),
// never keyed by card type — two cards of the same type can sit on the stack at once.
// ============================================================

// Context carries the live controller (push/pop/reset) down to whatever a card renders,
// so a deep child can drill without the surface prop-threading a callback through every level.
const RightStackCtx = React.createContext(null);
const useRightStackCtl = () => React.useContext(RightStackCtx);

// The PARENT (a surface like the seam index) calls this to OWN the pushed-layer array. It
// keeps reset() in the surface's hand for the center-select rule. `_seq` mints a push-unique
// key so the same card type can appear twice on the stack without a key collision (gotcha 3).
function useRightStack() {
  const [stack, setStack] = React.useState([]);
  const seq = React.useRef(0);
  return React.useMemo(() => ({
    stack,
    push: (layer) => setStack(s => [...s, { ...layer, _id: "L" + (++seq.current) }]),
    pop:  () => setStack(s => s.slice(0, -1)),
    reset: () => setStack([]),        // center peer-select → back to depth 1 on the new item
    depth: stack.length + 1,
  }), [stack]);
}

// A layer = { backLabel, render }. `root` is the depth-1 card (or null → empty state).
// Every layer stays MOUNTED and LAID OUT (absolute, stacked); only the top is visible. We
// hide the rest with visibility:hidden, NOT display:none — BECAUSE these layers are
// position:absolute, and Chrome wipes an overflow box's scrollTop across display:none ONLY when
// the box is absolutely positioned (a normal-flow box keeps its scroll — verified Chrome 149,
// so a plain display:none tab-wrapper like the News tab is safe). visibility keeps the absolute
// box laid out, so each layer's own scroll survives a push/pop and restore-on-pop is free. The
// back link pops; the body (not the bar) is the scroll container.
// `inline` = render WITHOUT the fixed .zinspect panel — a plain relative box that fills its
// parent. Desktop uses the fixed aside (the right column); the MOBILE sheet uses inline, so the
// stack lives INSIDE the sheet instead of position:fixed escaping it to the viewport edge.
function RightStack({ ctl, root, empty, className, inline }) {
  const Wrap = inline
    ? (kids) => <div className={"rstack rstack-inline " + (className || "")}>{kids}</div>
    : (kids) => <aside className={"zinspect rstack " + (className || "")}>{kids}</aside>;
  if (!root) return Wrap(empty);
  const layers = [{ root: true, backLabel: null, render: root.render, _id: root.key || "root" }, ...ctl.stack];
  const topIdx = layers.length - 1;
  return (
    <RightStackCtx.Provider value={ctl}>
      {Wrap(layers.map((L, i) => (
        <div key={L._id} className={"rstack-layer" + (i === topIdx ? " on" : "")} aria-hidden={i !== topIdx}>
          {!L.root && (
            <div className="rstack-bar">
              <button className="detail-back" onClick={ctl.pop} aria-label={"Back to " + (L.backLabel || "previous").toLowerCase()}>
                ‹ {L.backLabel || "Back"}
              </button>
            </div>
          )}
          <div className="rstack-body">{L.render()}</div>
        </div>
      )))}
    </RightStackCtx.Provider>
  );
}

// A swipe-dismiss bottom sheet for the mobile shell (reuses the shared hook from
// 20-shared-components so it matches every other sheet's feel). Plain scrim + rounded
// sheet; drag down or tap the scrim to close.
// `bare` = the child manages its own fill + scroll (an inline RightStack), so skip the padded
// scrolling .zsheet-body wrapper and let the child be the flex-fill instead.
function ZoneSheet({ title, onClose, children, bare }) {
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);
  return (
    <>
      <div className="zsheet-scrim" onClick={onClose} />
      <div ref={sheetRef} className={"zsheet" + (bare ? " zsheet--bare" : "")} role="dialog" aria-label={title || "Panel"}>
        <div className="zsheet-grab" aria-hidden="true"><div className="zsheet-handle" /></div>
        {title && <div className="zsheet-head">{title}</div>}
        {bare ? children : <div ref={scrollRef} className="zsheet-body">{children}</div>}
      </div>
    </>
  );
}

// Mobile bottom toolbar — one equal-width slot per collapsed zone (rail / inspect / etc.).
// `tools` = [{ key, label, icon, on, onTap }]; tapping opens that zone as a sheet over center.
function MobileBar({ tools }) {
  return (
    <nav className="zbar" aria-label="Panels">
      {(tools || []).map(t => (
        <button key={t.key} className={"zbar-btn" + (t.on ? " on" : "")} onClick={t.onTap}
                disabled={t.disabled} aria-label={t.label} title={t.label}>
          {t.icon}
          <span className="zbar-lbl">{t.label}</span>
        </button>
      ))}
    </nav>
  );
}

// The four-slot frame. Desktop renders the .z* three-column grid (the SAME classes News /
// Word study use today, so a migrated surface inherits their exact look). Mobile renders
// only the center inline; the rail + inspect collapse behind a bottom toolbar and open as
// sheets. `mobile` = { tools, sheet, sheetTitle, onCloseSheet }. The top nav is NOT part of
// this — it lives above, full width, and the inspect panel is reserved with padding, never
// drawn over the nav (handoff: new surfaces start structurally below the nav).
function Shell({ rail, center, inspect, mobile, isMobile, className, centerOnly, railClass, centerClass }) {
  if (!isMobile) {
    // `inspect` is expected to BE its own .zinspect aside (RightStack renders one; a static
    // panel is wrapped by the surface) — so render it directly, no second wrapper. The
    // .zshell padding-right still reserves its fixed strip. New-surface inspect starts BELOW
    // the nav (the .zinspect.rstack override), not the shipped surfaces' top:0 float.
    // railClass/centerClass let a migrated surface keep an extra per-slot class on the .zrail/
    // .zcenter element (Word study's "brail"/"center") so its DOM stays byte-identical.
    return (
      <div className={"zshell" + (centerOnly ? " center-only" : "") + (className ? " " + className : "")}>
        <aside className={"zrail" + (railClass ? " " + railClass : "")}>{rail}</aside>
        <main className={"zcenter" + (centerClass ? " " + centerClass : "")}>{center}</main>
        {!centerOnly && inspect}
      </div>
    );
  }
  const m = mobile || {};
  return (
    <div className={"zshell-m" + (className ? " " + className : "")}>
      <main className="zcenter-m">{center}</main>
      {!centerOnly && <MobileBar tools={m.tools} />}
      {m.sheet && <ZoneSheet title={m.sheetTitle} bare={m.sheetBare} onClose={m.onCloseSheet}>{m.sheet}</ZoneSheet>}
    </div>
  );
}
