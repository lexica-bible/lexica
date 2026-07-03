// ============================================================
// SHELL PURE LOGIC — the RightStack state transforms, factored OUT of the React hook
// so ONE copy is used by both the app (22-shell.jsx: useRightStack + RightStack) and the
// Node unit test (tests/test_rstack_logic.js). No React in here — plain array math only.
//
// Why a separate file: the transforms ARE the RightStack contract (PUSH-UNIQUE keys,
// pop-uncovers, center-select resets to depth-1), and that contract deserves a lock. It
// can't sit inside the hook (the hook needs React), and re-typing it in a test would be a
// second copy that could silently drift. So the hook CALLS these, the test IMPORTS these.
//
// This file is plain JS (no JSX): the browser bundle picks it up in filename order (21 <
// 22, so the helpers exist before the shell uses them); the export guard at the tail is a
// no-op in the browser (`module` is undefined there) and hands the functions to Node.
// ============================================================

// Mint a push-unique layer id. seq is a monotonically rising counter owned by the hook —
// each push gets its own id so two cards of the SAME type can sit on the stack without a
// React key collision (the gotcha the shell was built to avoid).
function rsNextId(seq) { return "L" + seq; }

// Push: append the layer with its minted id. Returns a NEW array (the old one is untouched).
function rsPush(stack, layer, id) { return [...stack, { ...layer, _id: id }]; }

// Pop: drop the top layer, uncovering the one beneath (which stayed mounted).
function rsPop(stack) { return stack.slice(0, -1); }

// Reset: back to depth 1. A center peer-select (choosing another item) calls this so the
// drill doesn't carry over onto the newly-selected item.
function rsReset() { return []; }

// The full layer list the panel renders: the depth-1 root first (keyed by its own stable
// key, or the literal "root"), then every pushed layer on top. depth = layers.length.
function rsLayers(rootRender, rootKey, stack) {
  return [{ root: true, backLabel: null, render: rootRender, _id: rootKey || "root" }, ...(stack || [])];
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { rsNextId, rsPush, rsPop, rsReset, rsLayers };
}
