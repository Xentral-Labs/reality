# Chat Orchestration Contract

Chat receives read and propose tools only. It reads fulfillment readiness before suggesting shipment, never treats a future date as dispatch permission, never invents invoice values, and explicitly hands every prepared proposal to authenticated human review. After execution, the next answer is based on a fresh canonical read.
