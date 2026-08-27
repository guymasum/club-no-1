const currencyFormatter = new Intl.NumberFormat("fr-BI", {
  style: "currency",
  currency: "BIF",
});

/** Formats an amount as Burundian Francs, e.g. 5000 -> "5 000 FBu". */
export function formatCurrency(amount) {
  return currencyFormatter.format(amount);
}
