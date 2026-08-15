import { useState } from "react";

import { deleteDocument } from "../api";

function DocumentList({
    documents,
    loading,
    error,
    onDelete,
    selectedDocumentId,
    onSelect,
}) {
    const [deleting, setDeleting] = useState("");
    const [deleteError, setDeleteError] = useState("");

    async function handleDelete(documentId) {
        try {
            setDeleting(documentId);
            setDeleteError("");

            await deleteDocument(documentId);
            await onDelete();
        } catch (err) {
            setDeleteError(err.message);
        } finally {
            setDeleting("");
        }
    }

    if (loading) {
        return <p className="document-list-status">Loading...</p>;
    }

    if (error) {
        return <p className="error">{error}</p>;
    }

    if (documents.length === 0) {
        return (
            <p className="document-list-status">
                No documents yet.
            </p>
        );
    }

    return (
        <div className="document-list">
            {deleteError && <p className="error">{deleteError}</p>}

            {documents.map((document) => (
                <div
                    className={`document-item ${selectedDocumentId === document.id ? "selected" : ""
                        }`}
                    key={document.id}
                >
                    <button
                        type="button"
                        className="document-select"
                        onClick={() => onSelect(document.id)}
                    >
                        {document.filename}
                    </button>

                    <button
                        type="button"
                        className="document-delete"
                        disabled={deleting === document.id}
                        onClick={() => handleDelete(document.id)}
                    >
                        {deleting === document.id ? "..." : "Delete"}
                    </button>
                </div>
            ))}
        </div>
    );
}

export default DocumentList;