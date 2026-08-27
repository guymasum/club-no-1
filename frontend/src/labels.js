// Stored values (category, role) stay in English in the database/API —
// these map them to French for display only.

// 'drink' is kept for any product created before the beer/wine/whisky split.
const CATEGORY_LABELS = { beer: "Bière", wine: "Vin", whisky: "Whisky", food: "Plat", drink: "Boisson" };
const ROLE_LABELS = { waiter: "Serveur", admin: "Administrateur" };

export function categoryLabel(category) {
  return CATEGORY_LABELS[category] || category;
}

export function roleLabel(role) {
  return ROLE_LABELS[role] || role;
}
