export function vehicleMatches(notice, vehicle, year) {
  if (!vehicle) return true;
  return Boolean(notice.transport?.vehicles.some(([make, model, listedYear]) =>
    make + ' ' + model === vehicle && (!year || String(listedYear) === year)));
}
