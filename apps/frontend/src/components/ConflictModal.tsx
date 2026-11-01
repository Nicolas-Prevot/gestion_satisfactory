import type { ConflictResponse } from "../lib/types";

type ConflictModalProps = {
  conflict: ConflictResponse | null;
  onClose: () => void;
  onRefresh: () => void;
};

export function ConflictModal({ conflict, onClose, onRefresh }: ConflictModalProps) {
  if (!conflict) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h3>Concurrent Edit Conflict</h3>
        <p>
          Another user changed this line before your save. Refresh the entity and retry with your local draft.
        </p>
        <p>
          Conflicting fields: {conflict.conflicting_fields.length ? conflict.conflicting_fields.join(", ") : "version"}
        </p>
        <details>
          <summary>Server snapshot</summary>
          <pre>{JSON.stringify(conflict.server, null, 2)}</pre>
        </details>
        <details>
          <summary>Your payload</summary>
          <pre>{JSON.stringify(conflict.client, null, 2)}</pre>
        </details>
        <div className="modal-actions">
          <button type="button" onClick={onRefresh}>
            Refresh data
          </button>
          <button type="button" onClick={onClose} className="secondary">
            Keep editing
          </button>
        </div>
      </div>
    </div>
  );
}
