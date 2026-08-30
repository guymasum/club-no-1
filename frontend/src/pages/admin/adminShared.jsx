import { useState } from "react";
import { ApiError } from "../../api.js";

export function useAsyncAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const run = async (fn) => {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, run };
}

export const PRODUCT_CATEGORIES = [
  { value: "beer", label: "Bière" },
  { value: "wine", label: "Vin" },
  { value: "whisky", label: "Whisky" },
  { value: "food", label: "Plat" },
];

/** Stock item picker + "portions per sale" input, shared by the create and
 * inline-edit forms. `state`/`setState` hold { stock_item_id, portions_per_sale }
 * where stock_item_id is "" for "no tracking" or a stock_item_id as a string. */
export function StockLinkFields({ stockItems, state, setState }) {
  return (
    <>
      <label className="muted">Suivi de stock (optionnel)</label>
      <select
        value={state.stock_item_id}
        onChange={(e) => setState({ ...state, stock_item_id: e.target.value })}
      >
        <option value="">Aucun suivi</option>
        {stockItems.map((s) => (
          <option key={s.stock_item_id} value={s.stock_item_id}>
            {s.name}
          </option>
        ))}
      </select>
      {state.stock_item_id && (
        <>
          <label className="muted">Portions consommées par vente</label>
          <input
            type="number"
            min="1"
            step="1"
            value={state.portions_per_sale}
            onChange={(e) => setState({ ...state, portions_per_sale: e.target.value })}
          />
        </>
      )}
    </>
  );
}

export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}
