# Data model

No new tables, columns or migrations. Receipt creates existing Movement and BusinessEvent linked to the supplier Commitment. Release changes the selected Reservation from active to released and emits its existing event. Quantity on a released reservation remains recorded. ChangeProposal stores reviewed intent/state/token in existing metadata. Derived reservation context is not an additional FK or handler argument.
