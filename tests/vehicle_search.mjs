import assert from 'node:assert/strict';
import test from 'node:test';
import {vehicleMatches} from '../web/vehicles.mjs';

const notice = {transport: {vehicles: [['FORD','F-150','2025'], ['FORD','ESCAPE','2024']]}};
test('the model and year must belong to the same vehicle row', () => {
  assert.equal(vehicleMatches(notice, 'FORD F-150', '2024'), false);
  assert.equal(vehicleMatches(notice, 'FORD F-150', '2025'), true);
  assert.equal(vehicleMatches(notice, 'FORD ESCAPE', ''), true);
  assert.equal(vehicleMatches({title:'FORD ESCAPE'}, 'FORD ESCAPE', ''), false);
  assert.equal(vehicleMatches({org:'CFIA'}, '', ''), true);
});
